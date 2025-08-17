# Google Places API Integration Guide

## 🎯 Overview

This guide explains how to use the enhanced Google Places API integration to automatically fetch farm shops with real images. The system is already built into the existing pipeline and will significantly enhance the user experience with authentic, high-quality photos.

## ✅ Benefits of Google Places Integration

- **📸 Real Images**: Authentic photos of actual farm shops
- **🔄 Automatic Updates**: Images stay current as businesses update their listings
- **📊 Rich Data**: Additional information like ratings, reviews, and business details
- **🌍 Global Coverage**: Access to millions of business listings worldwide
- **⚡ Fast Implementation**: Quick setup with existing Google infrastructure

## 🔧 Setup Instructions

### 1. **Get Google Places API Key**

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable billing (required for API usage)

#### Step 2: Enable Places API
1. Go to "APIs & Services" > "Library"
2. Search for "Places API"
3. Click "Enable"

#### Step 3: Create API Key
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the generated API key

#### Step 4: Restrict API Key (Recommended)
1. Click on the created API key
2. Under "Application restrictions", select "HTTP referrers"
3. Add your domain: `*.farmcompanion.co.uk/*`
4. Under "API restrictions", select "Restrict key"
5. Select "Places API" from the list

### 2. **Install Required Dependencies**

```bash
# Install Python dependencies
pip install requests pillow

# Optional: For Cloudinary integration
pip install cloudinary
```

### 3. **Set Environment Variables**

```bash
# Set Google Places API key
export GOOGLE_PLACES_API_KEY="your_api_key_here"

# Optional: Set Cloudinary credentials for image hosting
export CLOUDINARY_CLOUD_NAME="your_cloud_name"
export CLOUDINARY_API_KEY="your_api_key"
export CLOUDINARY_API_SECRET="your_api_secret"
```

### 4. **Run the Enhanced Pipeline**

```bash
# Run the complete pipeline with image fetching
./google_places.sh

# Or run manually
python3 src/google_places_fetch.py
cp dist/farms.uk.json ../farm-frontend/public/data/farms.uk.json
```

## 📊 API Usage & Costs

### **Google Places API Pricing**
- **Text Search**: $0.017 per request
- **Place Details**: $0.017 per request
- **Place Photos**: $0.007 per request

### **Estimated Costs for 1000 Farm Shops**
- Text Search: 1000 × $0.017 = $17
- Place Details: 1000 × $0.017 = $17
- Photos (3 per shop): 3000 × $0.007 = $21
- **Total**: ~$55 for 1000 shops

### **Rate Limiting**
- **Queries per second**: 10 QPS
- **Daily limit**: 100,000 requests
- **Monthly limit**: 2,000,000 requests

## 🔄 Implementation Workflow

### **Phase 1: Test Integration**
```bash
# Test with existing pipeline
./google_places.sh
```

### **Phase 2: Monitor Results**
```bash
# Check the generated data
ls -la dist/
cat dist/farms.uk.json | jq '.[0] | {name, images}'
```

### **Phase 3: Automated Updates**
```python
# Set up cron job for regular updates
0 2 * * 0 /path/to/python3 /path/to/google_places_images_advanced.py
```

## 🛠️ Customization Options

### **1. Image Processing**

```python
# Customize image dimensions
target_width = 800
target_height = 600

# Adjust quality settings
image.save(output_buffer, format='JPEG', quality=85, optimize=True)
```

### **2. Search Optimization**

```python
# Improve search accuracy
query = f"{shop_name} farm shop {address}"
params = {
    'query': query,
    'key': self.api_key,
    'type': 'establishment',
    'location': f"{lat},{lng}",
    'radius': 5000  # 5km radius
}
```

### **3. Image Selection**

```python
# Prioritize certain photo types
def select_best_photos(photos):
    """Select the best photos based on size and relevance"""
    sorted_photos = sorted(photos, key=lambda x: x.get('width', 0), reverse=True)
    return sorted_photos[:3]
```

## 🔒 Security & Best Practices

### **1. API Key Security**
- ✅ Never commit API keys to version control
- ✅ Use environment variables
- ✅ Restrict API keys to specific domains
- ✅ Monitor API usage regularly

### **2. Rate Limiting**
- ✅ Implement delays between requests
- ✅ Handle API quota exceeded errors
- ✅ Use exponential backoff for retries

### **3. Error Handling**
```python
try:
    response = self.session.get(url, params=params)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"API request failed: {e}")
    return None
```

## 📈 Monitoring & Analytics

### **1. Track API Usage**
```python
# Log API requests for monitoring
logger.info(f"API request: {endpoint} for {shop_name}")
```

### **2. Success Metrics**
- Images found per shop
- Image quality scores
- API response times
- Error rates

### **3. Cost Monitoring**
- Daily API usage
- Monthly costs
- Cost per image

## 🚀 Production Deployment

### **1. Environment Setup**
```bash
# Production environment variables
GOOGLE_PLACES_API_KEY=your_production_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### **2. Automated Scripts**
```bash
#!/bin/bash
# deploy_images.sh
cd /path/to/farm-pipeline
source .env
python3 google_places_images_advanced.py
```

### **3. Monitoring**
```bash
# Check script logs
tail -f /var/log/farm-images.log

# Monitor API usage
gcloud auth application-default print-access-token
```

## 🔄 Integration with Existing Workflow

### **1. Data Pipeline Integration**
```python
# Add to existing farm data pipeline
def update_farm_images():
    """Update farm images as part of regular data refresh"""
    importer = GooglePlacesImageImporter(api_key)
    farms = load_farms_data()
    
    for farm in farms:
        if not farm.get('images'):
            images = importer.process_shop_images(farm)
            if images:
                farm['images'] = images
    
    save_farms_data(farms)
```

### **2. Frontend Integration**
```typescript
// The frontend is already ready to display images
// Just ensure the data includes the 'images' field
interface FarmShop {
  images?: string[]
  // ... other fields
}
```

## 🐛 Troubleshooting

### **Common Issues**

#### **1. API Key Errors**
```
Error: REQUEST_DENIED
```
**Solution**: Check API key restrictions and billing

#### **2. No Places Found**
```
Warning: No place found for: Shop Name
```
**Solution**: Improve search query or check business name accuracy

#### **3. Rate Limiting**
```
Error: OVER_QUERY_LIMIT
```
**Solution**: Implement delays and retry logic

#### **4. Image Download Failures**
```
Error: Error downloading image
```
**Solution**: Check network connectivity and image URL validity

### **Debug Mode**
```python
# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

### **Google Places API Support**
- [Google Places API Documentation](https://developers.google.com/maps/documentation/places/web-service)
- [Google Cloud Support](https://cloud.google.com/support)

### **Implementation Support**
- Check script logs for detailed error messages
- Verify API key permissions
- Test with a single shop first
- Monitor API usage in Google Cloud Console

---

## 🎉 Next Steps

1. **Set up Google Cloud Project** and get API key
2. **Test with a few shops** using the basic script
3. **Configure image hosting** (Cloudinary recommended)
4. **Run full import** for all shops
5. **Set up automated updates** for new shops
6. **Monitor performance** and costs

**Status**: ✅ Scripts ready, needs API key setup
**Estimated Time**: 30 minutes for initial setup
**Cost**: ~$0.05 per shop for images
