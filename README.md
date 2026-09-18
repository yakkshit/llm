# FcukoffAI LLM Infrastructure Backup

This repository contains the production configuration for the custom fine-tuned Qwen2.5-7B HR Agent.

## 🚀 How to Restore
1. Clone this repo: `git clone https://github.com/yakkshit/llm.git`
2. Download the `cedz-hr-qwen-7b.Q4_K_M.gguf` file from Google Drive and place it in a `models/` folder.
3. Generate a new API key: `./gen_key.sh`
4. Start the services: `docker compose up -d`
5. Load the model: `docker exec -i fcukoffai-ollama ollama create cedz-hr-qwen -f - < Modelfile`
6. Get SSL: Run the Certbot command (see setup notes).
