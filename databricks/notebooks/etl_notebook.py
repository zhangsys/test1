# Databricks notebook source
dbutils.widgets.text("input_path", "")
dbutils.widgets.text("output_path", "")

input_path = dbutils.widgets.get("input_path")
output_path = dbutils.widgets.get("output_path")

df = spark.read.csv(input_path, header=True)
df.write.parquet(output_path) 