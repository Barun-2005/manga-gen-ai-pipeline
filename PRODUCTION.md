# MangaGen Production Configuration
# Complete production deployment guide

## 🚀 Production Checklist

### 1. Environment Setup
- [ ] Copy `.env.example` to `.env`
- [ ] Set all required API keys
- [ ] Configure MongoDB connection (or disable)
- [ ] Set production domain/port
- [ ] Enable HTTPS/SSL

### 2. Security
- [ ] Rate limiting enabled (`ENABLE_RATE_LIMIT=true`)
- [ ] Request size limits configured (10MB default)
- [ ] API keys secured (never commit .env)
- [ ] CORS origins restricted (not wildcard)
- [ ] MongoDB authentication enabled

### 3. Performance
- [ ] Image optimization enabled
- [ ] Caching configured (`.cache/` directory)
- [ ] Background task cleanup scheduled
- [ ] Health monitoring active
- [ ] Log rotation configured

### 4. Monitoring
- [ ] Health endpoint (`/health`) monitored
- [ ] Logs aggregated and searchable
- [ ] Error tracking enabled
- [ ] Resource alerts configured
- [ ] Uptime monitoring

### 5. Backup
- [ ] MongoDB backups automated
- [ ] Output directory backed up regularly
- [ ] Environment config backed up
- [ ] Database disaster recovery plan

---

## 📝 Production Environment Variables

```bash
# Required
GROQ_API_KEY=your_production_key

# Optional but recommended
MONGODB_URL=mongodb+srv://production-cluster
NVIDIA_IMAGE_API_KEY=your_nvidia_key

# Production settings
ENVIRONMENT=production
LOG_LEVEL=WARNING  # Less verbose in prod
ENABLE_DATABASE=true
ENABLE_RATE_LIMIT=true
RATE_LIMIT_CALLS=100  # Adjust based on load
```

---

## 🔧 Performance Tuning

### Image Generation
- Use NVIDIA FLUX for quality (requires API key)
- Pollinations is free but may rate limit under load
- Consider local models (Z-Image Turbo) for high volume

### Database
- Use MongoDB Atlas for production (managed)
- Enable connection pooling
- Index frequently queried fields
- Archive old jobs periodically

### Caching
- LLM responses cached 48hrs (`.cache/stories/`)
- Prompts cached 24hrs (`.cache/prompts/`)
- Clean cache daily in cron job

---

## 📊 Monitoring Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET /api/status/{job_id}` - Job status

---

## 🛡️ Security Best Practices

1. **Never expose API keys**
   - Use environment variables
   - Rotate keys regularly
   - Different keys for dev/prod

2. **Rate limiting**
   - Default: 10 req/60s per IP
   - Adjust based on usage patterns
   - Consider API key-based limits

3. **Input validation**
   - Max 10MB request size
   - Sanitize user inputs
   - Validate image formats

---

## 🔄 Backup Strategy

### Daily Backups
```bash
# MongoDB backup
mongodump --uri="$MONGODB_URL" --out=/backups/$(date +%Y%m%d)

# Output files
tar -czf outputs_backup_$(date +%Y%m%d).tar.gz outputs/
```

### Retention
- Daily: Keep 7 days
- Weekly: Keep 4 weeks
- Monthly: Keep 6 months

---

## 📈 Scaling Considerations

### Horizontal Scaling
- Load balancer (nginx/HAProxy)
- Multiple backend instances
- Shared MongoDB cluster
- Shared file storage (S3/MinIO)

### Vertical Scaling
- Increase memory for large images
- More CPU for parallel generation
- SSD for faster file I/O

---

## 🚨 Troubleshooting

### High CPU Usage
- Check concurrent job count
- Review image generation settings
- Enable caching

### Memory Issues
- Image optimization enabled?
- Old jobs cleaned up?
- Check for memory leaks in logs

### Slow Generation
- API rate limits hit?
- Network latency to APIs?
- Consider local models

---

## 📞 Support

Check logs in `logs/mangagen_YYYYMMDD.log` for detailed error information.
