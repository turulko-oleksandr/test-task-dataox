-- init-db.sql
-- Initialize PostgreSQL database for AutoRia scraper

-- Create additional databases if needed
-- CREATE DATABASE autoria_test;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create additional users if needed
-- CREATE USER read_only_user WITH PASSWORD 'readonly123';
-- GRANT CONNECT ON DATABASE autoria_db TO read_only_user;
-- GRANT USAGE ON SCHEMA public TO read_only_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO read_only_user;

-- Set search path
ALTER DATABASE autoria_db SET search_path TO public;