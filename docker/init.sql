-- docker/init.sql
CREATE USER faceuser WITH PASSWORD 'strongpassword';
CREATE DATABASE facesdb OWNER faceuser;
GRANT CONNECT ON DATABASE facesdb TO faceuser;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO faceuser;
-- No UPDATE, DELETE, DROP privileges
