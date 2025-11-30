package internal

import (
	"strings"
	"sync"

	"HW5/internal/api"
)

// Store is a thread-safe in-memory store for Products
// it has a int32 as key and save the api.Product as value
type Store struct {
	mu sync.RWMutex
	m  map[int32]api.Product
}

// create a new product
func NewStore() *Store {
	return &Store{m: make(map[int32]api.Product)}
}

// get product by id, return (product, true) if found,
// otherwise return (_, false)
func (s *Store) Get(id int32) (api.Product, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	p, ok := s.m[id]
	return p, ok
}

func (s *Store) Put(p api.Product) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.m[p.ProductId] = p
}

// if product not exist, create it and return true
// if product exist, update it and return false
func (s *Store) Upsert(p api.Product) (created bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, existed := s.m[p.ProductId]
	s.m[p.ProductId] = p
	return !existed
}

// Search searches products by matching query in SKU or Manufacturer
// It checks at most 'limit' products and returns matches
// Returns: (matching products, number of products checked)
func (s *Store) Search(query string, limit int) ([]api.Product, int) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	query = strings.ToLower(query)
	results := make([]api.Product, 0, 20) // return at most 20 results
	checked := 0

	// Iterate over all products, checking at most 'limit' products
	for _, p := range s.m {
		if checked >= limit {
			break
		}
		checked++

		// Search in SKU and Manufacturer (case insensitive)
		sku := strings.ToLower(p.Sku)
		manufacturer := strings.ToLower(p.Manufacturer)

		if strings.Contains(sku, query) || strings.Contains(manufacturer, query) {
			results = append(results, p)
			if len(results) >= 20 {
				// Already found 20 results, continue checking but do not add
				// Note: We continue counting checked but do not add to results
			}
		}
	}

	return results, checked
}
