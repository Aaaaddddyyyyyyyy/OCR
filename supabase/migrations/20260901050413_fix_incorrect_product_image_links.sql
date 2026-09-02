-- The previous uploader incorrectly assigned all images to product_id = 1.
-- Allow an image to temporarily have no product assignment.

ALTER TABLE public.product_images
ALTER COLUMN product_id DROP NOT NULL;

-- Remove the incorrect product relationship.
UPDATE public.product_images
SET product_id = NULL
WHERE product_id = 1;