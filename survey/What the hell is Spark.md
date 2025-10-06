## ❓ What the hell is Spark?

> **Question:**  
> _hey guys, what the hell is spark? I am pretty new and reading about spark online just creates more confusion._
>
> Let's say I:
>
> ```
> Ingest data --> transform it --> throw the data into BigQuery --> query data from the warehouse --> analysis
> ```
>
> Where do you use Spark during this process?
>
> From what I understand, SPARK is used to distribute the data handling jobs onto multiple machines. But it's still very confusing to me on how you would apply it in a real world context.
>
> Is it correct to say it's like when you need to count inventory, instead of one person spending all day to count items, you have 100 people count then adding up the number?

---

### 💡 **Answer**

First, the "100 people counting their stack and then adding up the results" is known as the **MapReduce** pattern, which is one of the predominant computation patterns in Big Data and therefore Spark.

**Apache Spark** is an engine designed to work in a distributed fashion. It takes a given task (like "count the inventory") and figures out the most efficient way to divide up that work among multiple worker machines, and also actually manages the work while it's being done.

- 🧠 **Planning component**: _Catalyst_ analyzes the work and generates an optimized work plan (in the form of a **directed acyclic graph**, or DAG).
- 🛠️ **Task management**: _Spark Scheduler_ orchestrates the work across the cluster.

Spark is popular because:
- 🚀 It has great performance and is highly tunable for specific workloads.
- 📈 It scales easily (add more workers for faster processing).
- 🗣️ Supports multiple languages: Python, SQL, Scala, Java, .NET, and R.
- 📂 Handles a wide variety of file formats and both structured/unstructured data.
- ⏱️ Supports both batch and streaming data.

**In your BigQuery example:**  
You could use Spark to perform the transformations on the data before putting it into BigQuery, and/or you could use Spark instead of BigQuery to query the data.