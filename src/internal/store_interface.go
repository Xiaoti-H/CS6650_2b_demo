package internal

import "HW5/internal/api"

// ProductStore defines the interface that all store implementations must satisfy
type ProductStore interface {
	Get(id int32) (api.Product, bool)
	Put(p api.Product)
	Upsert(p api.Product) bool
	Search(query string, limit int) ([]api.Product, int)
}
