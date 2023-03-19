---
title: Implementing Version Management of File Trees in PostgreSQL
date: 2023-03-19 20:37:00
tags: 
  - System design
  - PostgreSQL
---
# Overview

In the [previous post](https://www.notion.so/Implement-the-file-tree-in-PostgreSQL-using-ltree-126700c6ec7446a7b10762351418f71c), we discussed how to implement a file tree in PostgreSQL using `ltree`. Now, let's talk about how to integrate version control management for the file tree.

Version control is a process for managing changes made to a file tree over time. This allows for the tracking of its history and the ability to revert to previous versions, making it an essential tool for file management.

With version control, users have access to the most up-to-date version of a file, and changes are tracked and documented in a systematic manner. This ensures that there is a clear record of what has been done, making it much easier to manage files and their versions.

# Terminologies and Context

One **flawed** implementation involves storing all file metadata for every commit, including files that have not changed but are recorded as `NO_CHANGE`. However, this approach has a significant problem.

The problem with the simple and naive implementation of storing all file metadata for every commit is that it leads to significant write amplification, as even files that have not changed are recorded as `NO_CHANGE`. One way to address this is to avoid storing `NO_CHANGE` transformations when creating new versions, which can significantly reduce the write amplification.

This is good for querying, but bad for writing. When we need to fetch a specific version, the PostgreSQL engine only needs to scan the index with the condition `file.version = ?`. This is a very cheap cost in modern database systems. However, when a new version needs to be created, the engine must write $N$ rows of records into the log table (where $N$ is the number of current files). This will cause a write peak in the database and is unacceptable.

In theory, all we need to do is write the changed file. If we can find a way to fetch an arbitrary version of the file tree in $O(log(n))$ time, we can reduce unnecessary write amplification.

## Non Functional Requirements

## Scalability

Consider the worst-case scenario: a file tree with more than 1,000 files that is committed to more than 10,000 times. The scariest possibility is that every commit changes all files, causing a decrease in write performance compared to the efficient implementation. Storing more than 10 million rows in a single table can make it difficult to separate them into partitioned tables.

Suppose $N$ is the number of files, and $M$ is the number of commits. We need to ensure that the time complexity of fetching a snapshot of an arbitrary version is less than $O(N\cdot log(M))$. This is theoretically possible.

## Latency

In the worst case, the query can still respond in less than 100ms.

# Architecture

## Database Design

Illustration of data structures.

![Illustration of data structures.](/images/Implementing-Version-Management-of-File-Trees-in-PostgreSQL/file-tree-version-rdbms.png)

## Tech Details

> Subqueries appearing in `FROM` can be preceded by the key word `LATERAL`. This allows them to reference columns provided by preceding `FROM` items. (Without `LATERAL`, each subquery is evaluated independently and so cannot cross-reference any other `FROM` item.) — [https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-LATERAL](https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-LATERAL)
> 

PostgreSQL has a keyword called `LATERAL`. This keyword can be used in a join table to enable the use of an outside table in a `WHERE` condition. By doing so, we can directly tell the query optimizer how to use the index. Since data in a combined index is stored in an ordered tree, finding the maximum value or any arbitrarily value has a time complexity of $O(log(n))$.

Finally, we obtain a time complexity of $O(N \cdot log(M))$.

### Performance

Result: Fetching an arbitrary version will be done in tens of milliseconds.

```sql
explain analyse
select f.record_id, f.filename, latest.revision_id
from files f
inner join lateral (
        select *
        from file_logs fl
        where f.filename = fl.filename
          and f.record_id = fl.record_id
          -- and revision_id < 20000
        order by revision_id desc
        limit 1
    ) as latest
on f.record_id = 'f5c2049f-5a32-44f5-b0cc-b7e0531bf706';
```

```sql
Nested Loop  (cost=0.86..979.71 rows=1445 width=50) (actual time=0.040..18.297 rows=1445 loops=1)
  ->  Index Only Scan using files_pkey on files f  (cost=0.29..89.58 rows=1445 width=46) (actual time=0.019..0.174 rows=1445 loops=1)
        Index Cond: (record_id = 'f5c2049f-5a32-44f5-b0cc-b7e0531bf706'::uuid)
        Heap Fetches: 0
  ->  Memoize  (cost=0.57..0.65 rows=1 width=4) (actual time=0.012..0.012 rows=1 loops=1445)
"        Cache Key: f.filename, f.record_id"
        Cache Mode: binary
        Hits: 0  Misses: 1445  Evictions: 0  Overflows: 0  Memory Usage: 221kB
        ->  Subquery Scan on latest  (cost=0.56..0.64 rows=1 width=4) (actual time=0.012..0.012 rows=1 loops=1445)
              ->  Limit  (cost=0.56..0.63 rows=1 width=852) (actual time=0.012..0.012 rows=1 loops=1445)
                    ->  Index Only Scan Backward using file_logs_pk on file_logs fl  (cost=0.56..11.72 rows=158 width=852) (actual time=0.011..0.011 rows=1 loops=1445)
                          Index Cond: ((record_id = f.record_id) AND (filename = (f.filename)::text))
                          Heap Fetches: 0
Planning Time: 0.117 ms
Execution Time: 18.384 ms

```

### Test Datasets

This dataset simulates the worst-case scenario of a table with 14.6 million rows. Specifically, it contains 14.45 million rows representing a situation in which 1,400 files are changed 10,000 times.

```sql
-- cnt: 14605858
select count(0) from file_logs;
-- cnt: 14451538
select count(0) from file_logs where record_id = 'f5c2049f-5a32-44f5-b0cc-b7e0531bf706';

```

### Schema

```sql
create table public.file_logs
(
    file_key    ltree         not null,
    revision_id integer       not null,
    record_id   uuid          not null,
    filename    varchar(2048) not null,
    create_time timestamp,
    update_time timestamp,
    delete_time timestamp,
    blob_sha256 char(64),
    constraint file_logs_pk
        primary key (record_id, filename, revision_id)
);

alter table public.file_logs
    owner to postgres;

create table public.files
(
    record_id uuid          not null,
    filename  varchar(2048) not null,
    create_at timestamp     not null,
    primary key (record_id, filename)
);

alter table public.files
    owner to postgres;

```

# **Further Improvements**

We can implement this using an intuitive approach in a graph database.

![File tree version in graph database](/images/Implementing-Version-Management-of-File-Trees-in-PostgreSQL/file-tree-version-graph-database.png)