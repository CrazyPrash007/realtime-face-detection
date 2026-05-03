-- docker/init.sql
-- The 'faceuser' and 'facesdb' are automatically created by the postgres Docker image 
-- using the POSTGRES_USER and POSTGRES_DB environment variables. 

-- Apply least-privilege grants
-- (Note: faceuser is the db owner because of POSTGRES_USER, so it has implicit rights, 
-- but these grants enforce the read/write expectations from the design).
GRANT CONNECT ON DATABASE facesdb TO faceuser;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO faceuser;
-- No UPDATE, DELETE, DROP privileges
