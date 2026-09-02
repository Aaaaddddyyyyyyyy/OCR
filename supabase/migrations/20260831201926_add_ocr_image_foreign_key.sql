ALTER TABLE public.ocr_results
ADD CONSTRAINT ocr_results_image_id_fkey
FOREIGN KEY (image_id)
REFERENCES public.product_images(id)
ON DELETE CASCADE;