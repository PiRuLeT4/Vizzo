# 🚀 Comandos de Despliegue en Producción (vizzovr.com)

Ejecuta estos 3 comandos en la terminal de tu servidor Linux VPS cada vez que subas cambios al repositorio:

```bash
git pull
docker compose build --no-cache (opcional para reconstruir la imagen primero.)
docker compose up -d --build
```

---

### 💡 Notas Útiles

- **Ejecutar todo en un solo comando**:

  ```bash
  git pull && docker compose build && docker compose up -d
  ```

- **O bien usando el script ejecutable**:
  ```bash
  chmod +x deploy.sh
  ./deploy.sh
  ```
