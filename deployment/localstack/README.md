# LocalStack Deployment

## Start LocalStack

```bash
docker-compose up -d
```

## Test API

```bash
curl http://localhost:8080/health
curl "http://localhost:8080/products/search?q=alpha"
```

## Stop LocalStack

```bash
docker-compose down
```
