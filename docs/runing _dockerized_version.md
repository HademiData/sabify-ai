## Still inside sabify-ai

run

```
docker build -t sabify-ai .
```

Then run it:

```
docker run --rm -p 8082:8082 --env-file .env sabify-ai
```

You should see Uvicorn running on:

```

http://0.0.0.0:8082
```

Then in another terminal test:

```

curl http://localhost:8082/health
```

Expected:

```

{"status":"ok","service":"sabify-ai"}
```
