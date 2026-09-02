CREATE TABLE "public"."documents" (
  "id"                bigint                   GENERATED ALWAYS AS IDENTITY NOT NULL,
  "file_name"         text                     NOT NULL,
  "file_type"         text                     NOT NULL,
  "storage_path"      text                     NOT NULL,
  "page_count"        integer,
  "processing_status" text                     NOT NULL DEFAULT 'pending'::text,
  "created_at"        timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT "documents_pkey" PRIMARY KEY (id)
);

CREATE TABLE "public"."ocr_results" (
  "id"                 bigint                   GENERATED ALWAYS AS IDENTITY NOT NULL,
  "document_id"        bigint                   NOT NULL,
  "page_number"        integer,
  "raw_text"           text,
  "ocr_engine"         text,
  "average_confidence" numeric,
  "bounding_boxes"     jsonb,
  "created_at"         timestamp with time zone NOT NULL DEFAULT now(),
  "image_id"           bigint,
  CONSTRAINT "ocr_results_pkey" PRIMARY KEY (id)
);

CREATE TABLE "public"."product_images" (
  "id"           bigint                   GENERATED ALWAYS AS IDENTITY NOT NULL,
  "product_id"   bigint                   NOT NULL,
  "image_type"   text                     NOT NULL DEFAULT 'product'::text,
  "storage_path" text                     NOT NULL,
  "file_name"    text                     NOT NULL,
  "mime_type"    text,
  "width"        integer,
  "height"       integer,
  "created_at"   timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT "product_images_pkey" PRIMARY KEY (id)
);

CREATE TABLE "public"."product_specs" (
  "id"                 bigint                   GENERATED ALWAYS AS IDENTITY NOT NULL,
  "product_id"         bigint                   NOT NULL,
  "housing"            text,
  "wattage"            text,
  "led_source"         text,
  "colour_temperature" text,
  "beam_angle"         text,
  "system_lumens"      text,
  "product_size"       text,
  "cutout"             text,
  "ip_rating"          text,
  "outer_frame"        text,
  "created_at"         timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT "product_specs_pkey" PRIMARY KEY (id),
  CONSTRAINT "product_specs_product_id_key" UNIQUE (product_id)
);

CREATE TABLE "public"."products" (
  "id"           bigint                   GENERATED ALWAYS AS IDENTITY NOT NULL,
  "document_id"  bigint                   NOT NULL,
  "product_code" text                     NOT NULL,
  "product_name" text,
  "page_number"  integer,
  "created_at"   timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT "products_pkey" PRIMARY KEY (id)
);

ALTER TABLE "public"."ocr_results"
  ADD CONSTRAINT "ocr_results_document_id_fkey" FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;

ALTER TABLE "public"."products"
  ADD CONSTRAINT "products_document_id_fkey" FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;

ALTER TABLE "public"."product_images"
  ADD CONSTRAINT "product_images_product_id_fkey" FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;

ALTER TABLE "public"."product_specs"
  ADD CONSTRAINT "product_specs_product_id_fkey" FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;

CREATE POLICY "Allow insert product images" ON "public"."product_images"
  FOR INSERT
  TO "anon"
  WITH CHECK (true);

CREATE POLICY "Allow select product images" ON "public"."product_images"
  FOR SELECT
  TO "anon"
  USING (true);

CREATE POLICY "Allow document uploads 1y4g5bx_0" ON "storage"."objects"
  FOR INSERT
  TO "anon"
  WITH CHECK ((bucket_id = 'product-image'::text));

CREATE POLICY "Allow document uploads flreew_0" ON "storage"."objects"
  FOR INSERT
  TO "anon"
  WITH CHECK ((bucket_id = 'documents'::text));

CREATE POLICY "storage 1y4g5bx_0" ON "storage"."objects"
  FOR INSERT
  TO "anon", "authenticated"
  WITH CHECK ((bucket_id = 'product-image'::text));

GRANT DELETE, INSERT, MAINTAIN, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE ON TABLE "public"."documents" TO "anon", "authenticated", "postgres", "service_role";

GRANT DELETE, INSERT, MAINTAIN, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE ON TABLE "public"."ocr_results" TO "anon", "authenticated", "postgres", "service_role";

GRANT DELETE, INSERT, MAINTAIN, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE ON TABLE "public"."product_images" TO "anon", "authenticated", "postgres", "service_role";

GRANT DELETE, INSERT, MAINTAIN, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE ON TABLE "public"."product_specs" TO "anon", "authenticated", "postgres", "service_role";

GRANT DELETE, INSERT, MAINTAIN, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE ON TABLE "public"."products" TO "anon", "authenticated", "postgres", "service_role";

