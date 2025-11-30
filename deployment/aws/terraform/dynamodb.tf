# DynamoDB table for storing products
resource "aws_dynamodb_table" "products" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "product_id"

  attribute {
    name = "product_id"
    type = "N"
  }

  tags = {
    Name = "${var.project_name}-products-table"
  }
}
