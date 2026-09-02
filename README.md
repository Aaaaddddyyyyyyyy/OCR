# OCR Product Retrieval System

An AI-powered product catalog retrieval system that processes PDF catalogs, extracts product information using OCR, stores structured data and product images in Supabase, and provides hybrid product search with grounded AI-generated answers using Groq.

---

## Overview

This project converts unstructured PDF product catalogs into a searchable product database.

The system performs:

1. PDF ingestion
2. OCR processing
3. Product extraction
4. Product specification extraction
5. Product image extraction
6. Product-image mapping
7. Supabase storage and database persistence
8. 384-dimensional semantic embeddings
9. Structured attribute search
10. Semantic search
11. Hybrid Search V3
12. FastAPI-based product APIs
13. Groq-powered natural language answers

The AI answer layer is grounded strictly in retrieved catalog data to reduce hallucinations.

---

## Architecture

```text
                         PDF PRODUCT CATALOG
                                  |
                                  v
                         PDF Processing
                                  |
                                  v
                            OCR Engine
                       Tesseract + PyTesseract
                                  |
                                  v
                       Product Extraction
                                  |
                                  v
                  Specification Normalization
                                  |
                     +------------+------------+
                     |                         |
                     v                         v
               Product Data               Product Images
                     |                         |
                     |                  Image Extraction
                     |                  + Validation
                     |                         |
                     +------------+------------+
                                  |
                                  v
                              Supabase
                         /        |        \
                        /         |         \
                       v          v          v
                  Products      Specs      Images
                       |
                       v
                384-D Embeddings
                       |
             +---------+---------+
             |                   |
             v                   v
      Structured Search    Semantic Search
             |                   |
             +---------+---------+
                       |
                       v
                 Hybrid Search V3
                       |
                       v
                    FastAPI
                       |
                       v
                  Context Builder
                       |
                       v
                      Groq
                       |
                       v
              Grounded AI Answer