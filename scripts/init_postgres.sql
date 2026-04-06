CREATE USER storage_agent_user WITH PASSWORD 'storage_agent_password';
CREATE DATABASE "storage-agent" OWNER storage_agent_user;
GRANT ALL PRIVILEGES ON DATABASE "storage-agent" TO storage_agent_user;
