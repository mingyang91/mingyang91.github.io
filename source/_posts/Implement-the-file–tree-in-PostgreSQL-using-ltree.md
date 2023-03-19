---
title: Implement the file tree in PostgreSQL using ltree
date: 2023-03-19 18:18:18
tags: 
  - System design
  - PostgreSQL
---
# Implement the file tree in PostgreSQL using ltree

# Background

A file tree is a hierarchical structure used to organize files and directories on a computer. It allows users to easily navigate and access their files and folders, and is commonly used in operating systems and file management software.

But implementing file trees in traditional RDBMS like MySQL can be a challenge due to the lack of support for hierarchical data structures. However, there are workarounds such as using nested sets or materialized path approaches. Alternatively, you could consider using NoSQL databases like MongoDB or document-oriented databases like Couchbase, which have built-in support for hierarchical data structures.

It is possible to implement a file tree in PostgreSQL using the `ltree` datatype provided by PostgreSQL. This datatype can help us build the hierarchy within the database.

# TL;DR

## Pros

- Excellent performance!
- No migration is needed for this, as no new columns will be added. Only a new expression index needs to be created.

## Cons

- Need additional mechanism to create virtual folder entities.(only if you need to show the folder level)
- There are limitations on the file/folder name length.(especially in non-ASCII characters)

## Limitation

The maximum length for a file or directory name is limited, and in the worst case scenario where non-ASCII characters(Chinese) and alphabets are interlaced, it can not be longer than **33** characters. Even if all the characters are Chinese, the name can not exceed **62** characters in length.

Based on PostgreSQL [documentation](https://www.postgresql.org/docs/current/ltree.html#id-1.11.7.32.5), the label path can not exceed 65535 labels. However, in most cases, this limit should be sufficient and it is unlikely that you would need to nest directories to such a deep level.

```sql
select escape_filename_for_ltree(
    '一0二0三0四0五0六0七0八0九0十0' ||
    '一0二0三0四0五0六0七0八0九0十0' ||
    '一0二0三0四0五0六0七0八0九0十0' ||
    '一0二0'
); -- worst case len 34
select escape_filename_for_ltree(
    '一二三四五六七八九十' ||
    '一二三四五六七八九十' ||
    '一二三四五六七八九十' ||
    '一二三四五六七八九十' ||
    '一二三四五六七八九十' ||
    '一二三四五六七八九十' ||
    '一二三'
); -- Chinese case len 63
```

```
[42622] ERROR: label string is too long Detail: Label length is 259, must be at most 255, at character 260. Where: PL/pgSQL function escape_filename_for_ltree(text) line 5 at SQL statement
```

# How to use

Build expression index

```sql
CREATE INDEX idx_file_tree_filename ON files using gist (escape_filename_for_ltree(filename));
```

Example Query

```sql
explain analyse
select filename
from files
where escape_filename_for_ltree(filename) ~ 'ow.*{1}'
  and record_id = '1666bad1-202c-496e-bb0e-9664ce3febcb';
```

Query Result

```
ow/ros_00000000_2022-03-02-12-55-19_330.bag
ow/ros_00011426_2022-08-15-19-24-11_0.bag
ow/ros_00019378_2022-08-12-18-40-06_0.bag
ow/ros_00011426_2022-08-15-19-24-11_0.bag
ow/ros_00011426_2022-08-15-19-24-11_0.bag.coscene-reserved-index
```

Query Explain

```sql
Bitmap Heap Scan on files  (cost=32.12..36.38 rows=1 width=28) (actual time=0.341..0.355 rows=8 loops=1)
  Recheck Cond: ((record_id = '1666bad1-202c-496e-bb0e-9664ce3febcb'::uuid) AND (escape_filename_for_ltree((filename)::text) <@ 'ow'::ltree))
  Heap Blocks: exact=3
  ->  BitmapAnd  (cost=32.12..32.12 rows=1 width=0) (actual time=0.323..0.324 rows=0 loops=1)
        ->  Bitmap Index Scan on idx_file_tree_record_id  (cost=0.00..4.99 rows=93 width=0) (actual time=0.051..0.051 rows=100 loops=1)
              Index Cond: (record_id = '1666bad1-202c-496e-bb0e-9664ce3febcb'::uuid)
        ->  Bitmap Index Scan on idx_file_tree_filename  (cost=0.00..26.88 rows=347 width=0) (actual time=0.253..0.253 rows=52 loops=1)
              Index Cond: (escape_filename_for_ltree((filename)::text) <@ 'ow'::ltree)
Planning Time: 0.910 ms
Execution Time: 0.599 ms

```

# Explaination

PostgreSQL's LTREE data type allows you to use a sequence of alphanumeric characters and **underscores** on the label, with a maximum length of 256 characters. So, we get a special character **underscore** that can be used as a notation to **build our escape rules** within the label.

**Slashes(`/`)** will be **replaced** with **dots(`.`)**. I think it does not require further explanation.

Initially, I attempted to encode all non-alphabetic characters into their Unicode hex format. However, after receiving advice from @Juchao Song , I discovered that using **base64** encoding can be more efficient in terms of information entropy. Ultimately, I decided to use **base62** encoding instead to ensure that no illegal characters are produced and to achieve the maximum possible information entropy.

This is the final representation of the physical data that will be stored in the index of PostgreSQL.

```sql
select escape_filename_for_ltree('root/folder1/机器人仿真gazebo11-noetic集成ROS1/state.log');
-- result:
-- root.folder1._1hOBTVt5n7EhFWzIbUcjT_gazebo11_j_noetic_1Aw3qhY48_ROS1.state_k_log

```

# Further

If you want to store an isolated file tree in the same table, one thing you need to do is prepend the isolation key as the first label of the ltree. For example:

```sql
select escape_filename_for_ltree('<put_user_id_in_there>' || '/' || '<path_to_file>');
```

By doing this, you will get the best query performance.

# Summary

This document explains how to implement a file tree in PostgreSQL using the `ltree` datatype. The `ltree` datatype can help build the hierarchy within the database, and an expression index needs to be created. There are some limitations on the file/folder name length, but the performance is excellent. The document also provides PostgreSQL functions for escaping and encoding file/folder names.

# Appendix: PostgreSQL Functions

## Entry function (immutable is required)

```sql
CREATE OR REPLACE FUNCTION escape_filename_for_ltree(filename TEXT)
    RETURNS ltree AS
$$
DECLARE
    escaped_path ltree;
BEGIN
    select string_agg(escape_part(part), '.')
    into escaped_path
    from (select regexp_split_to_table as part
          from regexp_split_to_table(filename, '/')) as parts;

    return escaped_path;

END;
$$ LANGUAGE plpgsql IMMUTABLE;

```

## Util: Escape every part (folder or file)

```sql
create or replace function escape_part(part text) returns text as
$$
declare
    escaped_part text;
begin
    select string_agg(escaped, '')
    into escaped_part
    from (select case substring(sep, 1, 1) ~ '[0-9a-zA-Z]'
                     when true then sep
                     else '_' || base62_encode(sep) || '_'
                     end as escaped
          from (select split_string_by_alpha as sep
                from split_string_by_alpha(part)) as split) as escape;
    RETURN escaped_part;
end;
$$ language plpgsql immutable

```

## Util: Split a string into groups

Each group contains only alphabetic characters or non-alphabetic characters.

```sql
CREATE OR REPLACE FUNCTION split_string_by_alpha(input_str TEXT) RETURNS SETOF TEXT AS
$$
DECLARE
    split_str TEXT;
BEGIN
    IF input_str IS NULL OR input_str = '' THEN
        RETURN;
    END IF;

    WHILE input_str != ''
        LOOP
            split_str := substring(input_str from '[^0-9a-zA-Z]+|[0-9a-zA-Z]+');
            IF split_str != '' THEN
                RETURN NEXT split_str;
            END IF;
            input_str := substring(input_str from length(split_str) + 1);
        END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql

```

## Util: base62 encode function

By using the base62_encode function, we can create a string that meets the requirements of LTREE and achieves maximum information entropy.