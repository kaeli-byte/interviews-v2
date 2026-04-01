ALTER TABLE documents
  ALTER COLUMN content TYPE jsonb
  USING CASE
    WHEN content IS NULL OR btrim(content) = '' THEN '{}'::jsonb
    ELSE content::jsonb
  END;

ALTER TABLE documents
  ALTER COLUMN content SET DEFAULT '{}'::jsonb;
