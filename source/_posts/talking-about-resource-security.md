---
title: 浅谈资源安全
date: 2022-08-21 12:12:43
tags: 
  - Rust
  - Programming language
---
# 起因

这个月（2022年8月）于Rust二群与某人辩论，因为某人坚持认为 Rust 的所有权 `Ownership` 机制仅仅是等同于垃圾回收 `Garbage Collection` ，而我认为 `Ownership` 还解决了另一个困扰无数码农的问题：**资源安全**

# 定义

常见资源可以分为三大类：

- 文件
    - Socket
        - TCP
        - HTTP
        - JDBC
    - 文件系统
- 锁
    - 本地
    - 远程（Redis，RDBMS）
- 逻辑资源
    - Stream（背后可能是文件）
    - 日志区块或长链接起止符
    - 临时文件删除

而资源管理总共分三步，分别是：

1. 资源申请
2. 资源使用
3. 资源释放

这三个事件需要严格按顺序发生。

而资源安全关注的是:

- 在使用前已经正确初始化
- 使用后能被正确释放
- 释放后不能被再次使用

语言（语法）提供的资源管理有什么用呢？它给程序员一个强有力的保证，非极端情况下（断电等），资源释放逻辑必定会被执行。

# 资源管理的历史

## 史前

### C

```c
#include <stdio.h>
#include <stdlib.h>

int main()
{
   int num;
   FILE *fptr;

   if ((fptr = fopen("C:\\program.txt","r")) == NULL){
       printf("Error! opening file");

       // Program exits if the file pointer returns NULL.
       exit(1);
   }

   fscanf(fptr,"%d", &num);

   printf("Value of n=%d", num);
   fclose(fptr); 
  
   return 0;
}
```

早期的计算机语言并没有意识到资源管理问题，依然是指令式编码风格，需要程序员自己保证资源的申请与释放。同时那个年代软件系统并不复杂，再加上从业者素质普遍较高，所以资源管理问题不像今天这么突出。

## 语言结构(Language constructs)

后来，有些语言引入了异常机制，允许程序无视控制流语句自行中断并跳出，资源管理也变得复杂起来。支持抛出异常的语言通常使用 `try {} catch {} finally {}` 约束资源作用范围， `try` 关键字表示资源作用范围，无论程序以任何形式跳出， `finally` 关键字标记代码块都应当被确保执行，资源正确释放，代表语法： 

```java
FileReader fr = new FileReader(path);
BufferedReader br = new BufferedReader(fr);
try {
    return br.readLine();
} finally {
    br.close();
    fr.close();
}
```

## 销毁模式(Dispose pattern)

这个模式也是当今大部分有 GC 语言所支持的，比如 Java 语法关键字 `try`

据我所知 Java 所谓的资源安全只有 Java7 时代引入的 try-with-resource，资源需继承自`AutoCloseable`，可以在 `try(...) { ... code block ... }` 内放心使用，也就意味着异步代码没有任何保障。

```java
static String readFirstLineFromFile(String path) throws IOException {
    try (FileReader fr = new FileReader(path);
         BufferedReader br = new BufferedReader(fr)) {
        return br.readLine();
    }
}
```

## Resource Monad 模式

后续发展中诞生的较为安全的设计模式，将使用资源的同步或异步代码包裹在一个代码块中，使用结束后释放，这样可以避免在每次使用资源后手动关闭。

```java
public static <R> CompletionStage<R> use (Function<Resource, CompletionStage<R>> f) {
  return Resource.make()
    .thenCompose((res) -> f.apply(res)
      .handle((r, e) -> {
        res.close();
        if (e != null) throw new RuntimeException(e);
        return r;
      })
    );
}

use((res) -> {
  System.out.println(res);
  // 将业务逻辑编写到 CompletableFuture 内部执行
  return CompletableFuture.failedStage(new Exception("error"));
}).handle((r, e) -> {
  if (e != null) {
    System.out.println(e.getMessage());
  }
  return r;
});
```

以上方案都有一个缺陷，在使用过程中误将资源变量共享给其他代码段（闭包，回调，外部变量，无意中发送给队列 HTTP Response，例如如下 Java 代码。

```java
static HttpEntity fileEntity(String filename) throws IOException {
  try (FileReader fr = new FileReader(path);
       BufferedReader br = new BufferedReader(fr)) {
    return new HttpEntity(br);
  }
}
```

如果 `HttpEntity` 类并不是在创建时消费 `Reader` ，而是会等待 HTTP Body 传输时才开始读取字节流，那毫无疑问，这会造成访问已关闭资源，可能引起应用程序崩溃。

正确的写法如下

```java

// 伪代码
static HttpEntity fileEntity(String filename) throws IOException {
  final FileReader fr = new FileReader(path);
  final BufferedReader br = new BufferedReader(fr);
  return new HttpEntity(br) {
    public void close() {
      br.close();
      fr.close();
    }
  };
```

## RAII

### C++

> Move semantics make it possible to safely transfer resource ownership between objects, across scopes, and in and out of threads, while maintaining resource safety. — (since C++11)
> 

```rust
void f()
{
    vector<string> vs(100);   // not std::vector: valid() added
    if (!vs.valid()) {
        // handle error or exit
    }

    ifstream fs("foo");   // not std::ifstream: valid() added
    if (!fs.valid()) {
        // handle error or exit
    }

    // ...
} // destructors clean up as usual
```

C++ 提出了 RAII 这一先进概念，几乎解决了资源安全问题。但是受限于 C++ 诞生年代，早期 C++ 为了保证资源安全，只支持左值引用(LValue Reference) + Clone(Deep Copy) 语义，使得赋值操作会频繁深拷贝整个对象与频繁构造/析构资源，浪费了很多操作。C++11 开始支持右值引用，但是仍然需要实现右值引用(RValue Reference)的 Move(Shallow Copy)。同时，C++ 无法检查多次 move 的问题和 move 后原始变量仍然可用的问题。

```cpp
#include <iostream>
using namespace std;

class A{
    public:
        A(const string& str, int* arr):_str(str),_arr(arr){cout << "parameter ctor" << endl;}
        A(A&& obj):_str(std::move(obj._str)),_arr(std::move(obj._arr)){obj._arr = nullptr;cout << "move ctor" << endl;}
        A& operator =(A&& rhs){
            _str = std::move(rhs._str);
            _arr = std::move(rhs._arr);
            rhs._arr = nullptr;
            cout << "move assignment operation" << endl;
            return *this;
        }
        void print(){
            cout << _str << endl;
        }
        ~A(){
            delete[] _arr;
            cout << "dtor" << endl;
        }
    private:
        string _str;
        int* _arr;
};

int main(){
    int* arr = new int[6] {1,1,4,5,1,4};
    A a("Yajuu Senpai", std::move(arr)); // 错误的指针移动 --> STUPID MOVE!!
    A b(std::move(a));   // move ctor

    cout << "print a: ";
    a.print();           // a 失去所有权  --> CORRECT!!
    cout << "print b: ";
    b.print();           // b 获得所有权  --> CORRECT!!

    b = std::move(a);    // 二次移动

    cout << "print a: "; 
    a.print();           // ???
    cout << "print b: "; 
    b.print();           // ???
}
```

### Rust

继承自 **C++ RAII ，**当创建资源和使用资源不在同一个领域时，Rust 的 `move` / `borrow` 依然可以安心睡觉，这种语言级别的保证让我一个写 Scala 的看了都羡慕。

在Rust 中`move` 给别人就是别人负责 `drop`， `borrow` 给别人还是自己负责 `drop`，且编译器会根据生命周期检查，确保不会发生多次 `move`，也不会有超出拥有者(`owner`)的借用(`&borrow`)发生。责任划分很清晰，只要自己脑子清醒，完全不担心异步的时候会泄漏。

程序员无法显式 `delete`，只能遵守 Rust 语法，编译器依据变量生命周期将相关变量的 `drop` 插入到正确位置，通常是离开块级作用域的位置。

![Rust Drop](/images/rust-drop.png)

[https://doc.rust-lang.org/rust-by-example/scope/raii.html](https://doc.rust-lang.org/rust-by-example/scope/raii.html)

同步示例如下：

```rust
struct Entity {
  connection: &Connection
  file: File
}

impl Drop for Entity {
  fn drop(&mut self) {
    file.write(EOF); // <- 文件关闭前写入终止符
  }
}

let conn = makeConnection();
let file = openFile();
let entity = Entity {
  connection: &conn, // <- 将 conn 借用给 entity
  file: file // <- 将 file 所有权转移给 entity
} // <- 从此以后，file 将不可被访问
fn send(entity: Entity) {
  // logic
  return;
  // <- 编译器会在此处插入释放 entity
}
send(entity) // <- 将 entity 所有权移交给 send 函数
// <- 编译器会在此处插入释放 conn
// <- 因 entity 与 file 所有权已转移，此处不会重复释放 entity 与 file
```

异步示例如下：

```java
fn move_block() -> impl Future<Output = ()> {
    let my_string = "foo".to_string();
    async move { // <- my_string 被 move 到此 block scope
        // ...
        println!("{}", my_string); // <- my_string 在此处可以见
        // <- 编译器将在此处插入 my_string drop 代码 
    }
    // <- my_string 将不再可见，本函数失去 my_string 所有权，不再插入 drop 代码
}
```

**闭包捕获**造成的资源逃逸与将引用赋值给**类/结构体**帮助资源逃逸在语言本质上是同一个问题，所以 Rust 可以用相同的方法来处理它们。

# 总结

理论上来说垃圾回收器(**Garbage collector**)无法解决资源安全问题，可能有人会认为：

> “给 Java 语言添加 `Destructor` ，这样开发者就可以在析构函数中实现资源释放逻辑，交给 GC 在回收内存时自动调用 `destory()/dispose()` ，问题不就解决了吗？“
> 

实际上这条路是走不通的，GC 根据算法不同，所参考的策略也不同，其收集(`collect`)/释放(`free`)动作必定会执行，但没有保证什么时候会执行，以什么顺序执行。因为考察 GC 性能指标时，更关注的是吞吐量而不是回收实时性，如果内存没有压力，GC 倾向于不回收。

这一行为可能会导致意想不到的后果，比如业务逻辑 A 结束时，文件资源对象的引用计数已经为零，通知下一个逻辑 B 可以处理此文件，而 B 尝试打开文件时却发现文件不完整，因为关闭文件的系统调用尚未被 GC 执行😵。

Rust 给出了一套完善的解决方案，它不仅解决了诸多内存安全问题，还顺带解决了资源安全问题。基于所有权机制和严格的编译器检查，强迫程序员写出资源安全的代码，仅需要程序员正确实现 `impl Drop for [...]` 。

我认为 Rust 实现的所有权与 RAII 是当下最完善的资源管理机制。

- 与 `try-catch-finally` 相比，不需要在每次使用资源时，都格外小心是否双重释放(`double delete` 这在 Java 中是个很常见且令人头痛的问题)。
- 与 `ResourceMonad` 相比，不会产生资源逃逸。
- 是一门全新的语言，不像 C++ 一样有沉重的历史包袱。

即使不使用 Rust 编码，依然可以借鉴它的思想，因为其语法本身就是资源管理的最佳实践，学习它可以帮助自己在其他语言中避开错误的写法。