# Troubleshooting Guide

## Current Issue: MiWay API Connection Errors

### What's Happening?

When you start the app, you see:
```
❌ Connection error: ('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer'))
```

### Root Cause

**The MiWay servers are currently down or blocking connections.**

We've confirmed this with multiple tests:
- ✅ Our code is correct
- ✅ Headers are properly set  
- ❌ MiWay's `www.miapp.ca` returns `503 Service Unavailable`
- ❌ HTTPS connections fail during TLS handshake
- ❌ Even `curl` with insecure mode fails

### What Still Works ✅

Good news! Most of the app works because we have **static GTFS data loaded locally**:

1. **✅ Route Planning** - Find routes between stops
2. **✅ Stop Search** - All 4,089 stops available
3. **✅ Nearby Stops** - Location-based stop finding
4. **✅ Schedule Data** - Departure times and routes
5. **✅ Beautiful UI** - New sidebar layout!

### What Doesn't Work ❌

Features requiring real-time data from MiWay:

1. **❌ Live Bus Tracking** - No vehicle positions available
2. **❌ Real-time ETAs** - No trip updates
3. **❌ Service Alerts** - No alerts feed

### How the App Handles This

The app is designed to gracefully handle API outages:

1. **No Crashes** - App continues running
2. **Error Logging** - All errors logged to console
3. **User Notifications** - Alert banner shows "Live Data Unavailable"
4. **Auto-Retry** - Background worker keeps trying every 30 seconds
5. **Detailed Errors** - Console shows full error details

### Testing API Status

Run the health check anytime:

```bash
python3 health_check.py
```

This will test all 4 MiWay endpoints and show:
- ✅ Which endpoints are healthy
- ❌ Which are down
- ⚠️ If you're being rate-limited
- Response times and data sizes

Results are saved to `logs/health_check.log` for tracking.

### What to Do Now

#### Option 1: Wait for MiWay (Recommended)
- Keep the app running
- Use route planning features (they work!)
- Live tracking will automatically resume when APIs are back

#### Option 2: Monitor API Status
```bash
# Check every few hours
python3 health_check.py

# Or monitor continuously for 5 minutes
python3 health_check.py monitor 300 30
```

#### Option 3: Contact MiWay
If APIs are down for extended periods:
- Contact MiWay IT support
- Report API outage
- Ask for status updates

### Common Error Messages Explained

#### "Connection reset by peer"
**Meaning**: Server terminated connection during TLS handshake  
**Cause**: MiWay servers are down or blocking  
**Fix**: Wait for MiWay to fix their servers

#### "503 Service Unavailable"  
**Meaning**: Server is temporarily unable to handle requests  
**Cause**: MiWay server maintenance or issues  
**Fix**: Wait and retry later

#### "Rate limited" (429)
**Meaning**: Too many requests to API  
**Cause**: Exceeded request limits  
**Fix**: App will automatically slow down requests

### Development Tips

While APIs are down, you can still work on:
- UI improvements (sidebar looks great!)
- Route planning logic
- Stop search features
- Database queries
- Frontend polish

Live tracking features will need real API access to test.

### When APIs Come Back Online

The app will automatically:
1. ✅ Reconnect via background worker
2. ✅ Download latest vehicle positions
3. ✅ Update trip data and alerts
4. ✅ Hide the "Unavailable" banner
5. ✅ Resume live tracking

**No manual intervention needed!**

### Logs and Debugging

Check these for more info:

```bash
# View health check history
cat logs/health_check.log | tail -20

# Watch app console output
# (Already running - just look at terminal)

# Test API manually
curl -v https://www.miapp.ca/GTFS_RT/Vehicle/VehiclePositions.pb
```

### Questions?

**Q: Is this a bug in our code?**  
A: No, we've verified the code is correct. MiWay's servers are the issue.

**Q: How long until it's fixed?**  
A: We don't know - it's on MiWay's side. Could be minutes or hours.

**Q: Can I use the app?**  
A: Yes! Route planning works perfectly. Just no live tracking yet.

**Q: Will I lose data?**  
A: No, all static GTFS data (stops, routes, schedules) is safely stored locally.

**Q: Should I restart the app?**  
A: Not necessary. It will auto-reconnect when APIs are back.

---

**Remember**: This is a temporary server issue, not a code problem. Your app is working correctly! 🚌✨

