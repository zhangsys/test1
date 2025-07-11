// Databricks notebook source
// 这是一个 Scala 脚本示例
val data = Seq((1, "foo"), (2, "bar"))
val df = spark.createDataFrame(data).toDF("id", "value")
df.show() 