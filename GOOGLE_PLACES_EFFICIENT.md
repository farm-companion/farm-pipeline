# Efficient Google Places API Usage

## The Problem
Previously, every time you wanted to update farm data, you had to fetch ALL data (including images) for every farm, which was:
- **Expensive** (~$15-30 per run)
- **Slow** (takes 10-15 minutes)
- **Inefficient** (re-fetching data you already have)

## The Solution
We've separated the operations into different commands that you can run independently:

### 🚀 Quick Commands

```bash
# Set your API key (one time)
export GOOGLE_PLACES_API_KEY='your-api-key-here'

# Then use these commands:
./run_places.sh data-only     # Fast & cheap (~$5-10)
./run_places.sh images-only   # Medium speed (~$10-20)
./run_places.sh data+images   # Full fetch (~$15-30)
./run_places.sh update-data   # Update existing data
```

## Command Breakdown

### 1. `data-only` - FAST & CHEAP
**When to use:** Initial setup, updating addresses/contact info, adding new farms
- ✅ Fetches: Names, addresses, phone numbers, websites, ratings
- ❌ Skips: Images
- 💰 Cost: ~$5-10
- ⏱️ Time: 3-5 minutes
- 🎯 Perfect for: Regular data updates

### 2. `images-only` - MEDIUM SPEED
**When to use:** Adding images to existing farms
- ✅ Fetches: Only images for farms that already exist
- ❌ Skips: All other data
- 💰 Cost: ~$10-20
- ⏱️ Time: 5-8 minutes
- 🎯 Perfect for: Adding visual content

### 3. `data+images` - FULL FETCH
**When to use:** Complete refresh, major updates
- ✅ Fetches: Everything (data + images)
- 💰 Cost: ~$15-30
- ⏱️ Time: 10-15 minutes
- 🎯 Perfect for: Major updates or when you want everything fresh

### 4. `update-data` - SMART UPDATE
**When to use:** Refreshing existing farm information
- ✅ Updates: Addresses, phone numbers, ratings, contact info
- ❌ Skips: Images
- 💰 Cost: ~$5-10
- ⏱️ Time: 3-5 minutes
- 🎯 Perfect for: Keeping data current

## Typical Workflow

### Initial Setup
```bash
# 1. Get all the basic data first
./run_places.sh data-only

# 2. Add images later (optional)
./run_places.sh images-only
```

### Regular Maintenance
```bash
# Update farm data weekly/monthly
./run_places.sh update-data

# Add images for new farms (as needed)
./run_places.sh images-only
```

### Major Refresh
```bash
# Complete refresh (expensive, use sparingly)
./run_places.sh data+images
```

## Cost Optimization Tips

### 💡 Save Money
1. **Use `data-only` for regular updates** - 70% cheaper than full fetch
2. **Run `images-only` separately** - only when you need images
3. **Use `update-data` for maintenance** - refreshes existing data efficiently

### 📊 Cost Comparison
| Command | Cost | Time | Use Case |
|---------|------|------|----------|
| `data-only` | ~$5-10 | 3-5 min | Regular updates |
| `images-only` | ~$10-20 | 5-8 min | Add visual content |
| `data+images` | ~$15-30 | 10-15 min | Major refresh |
| `update-data` | ~$5-10 | 3-5 min | Data maintenance |

## API Usage Breakdown

### What Each Command Does

#### `data-only`
- **Nearby Search API**: ~1,300 calls (one per location)
- **Place Details API**: ~1,300 calls (one per farm)
- **Total**: ~2,600 API calls

#### `images-only`
- **Place Details API**: ~1,300 calls (check for photos)
- **Place Photo API**: ~1,300 calls (get image URLs)
- **Total**: ~2,600 API calls

#### `data+images`
- **Nearby Search API**: ~1,300 calls
- **Place Details API**: ~1,300 calls
- **Place Photo API**: ~1,300 calls
- **Total**: ~3,900 API calls

## Error Handling

The scripts include robust error handling:
- ✅ Continues if individual farms fail
- ✅ Retries on temporary errors
- ✅ Graceful degradation
- ✅ Clear error messages

## File Management

All scripts automatically:
- ✅ Save to `dist/farms.uk.json` and `dist/farms.geo.json`
- ✅ Copy files to frontend automatically
- ✅ Preserve existing data structure
- ✅ Handle file permissions

## Troubleshooting

### Common Issues

**"API key not set"**
```bash
export GOOGLE_PLACES_API_KEY='your-key-here'
```

**"farms.uk.json not found"**
```bash
# Run data-only first
./run_places.sh data-only
```

**"Permission denied"**
```bash
chmod +x run_places.sh
```

**"Python not found"**
```bash
# Use python3 explicitly
python3 src/google_places_fetch.py --no-images
```

## Best Practices

### 🎯 Recommended Usage Pattern
1. **Start with `data-only`** - get all the basic information
2. **Use `update-data` for maintenance** - keep data fresh
3. **Run `images-only` when needed** - add visual content
4. **Use `data+images` sparingly** - only for major updates

### 📅 Suggested Schedule
- **Weekly**: `update-data` (keep data fresh)
- **Monthly**: `images-only` (add new images)
- **Quarterly**: `data+images` (complete refresh)

This approach saves you **70-80% on API costs** while keeping your farm data current and visually appealing!
