# 🚀 Vercel Deployment Guide

## Quick Setup Steps

### 1. Connect GitHub to Vercel
1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "Add New Project"
3. Import the `Ohmdatazwld5/Voice-Scheduling-Agent` repository
4. Vercel will auto-detect the framework

### 2. Configure Environment Variables
In the Vercel project settings, add these environment variables:

```
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://your-app.vercel.app/api/oauth/callback
```

⚠️ **IMPORTANT**: Replace `your-app` with your actual Vercel app URL after first deployment!

### 3. Deploy
1. Click "Deploy"
2. Wait for build to complete
3. Copy your deployment URL (e.g., `https://voice-scheduling-agent.vercel.app`)

### 4. Update Google OAuth Settings
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to: APIs & Services → Credentials
3. Select your OAuth 2.0 Client ID
4. Add to **Authorized redirect URIs**:
   ```
   https://your-actual-vercel-url.vercel.app/api/oauth/callback
   ```
5. Save changes

### 5. Update Environment Variable (Final Step)
1. Back in Vercel, go to Settings → Environment Variables
2. Update `GOOGLE_REDIRECT_URI` to match your actual Vercel URL:
   ```
   https://your-actual-vercel-url.vercel.app/api/oauth/callback
   ```
3. Redeploy to apply changes

## 🔍 Verification Checklist

- [ ] Repository connected to Vercel
- [ ] All 4 environment variables configured
- [ ] First deployment successful
- [ ] Google OAuth redirect URI updated
- [ ] `GOOGLE_REDIRECT_URI` env var matches actual URL
- [ ] Redeployed after env var update
- [ ] Test voice scheduling from live URL

## 🛠️ Troubleshooting

### Build Fails
- Check that all dependencies in `requirements.txt` are compatible
- Verify Python version (should use 3.9+)

### OAuth Errors
- Ensure redirect URI in Google Console exactly matches the one in env vars
- Check that Google Calendar API is enabled

### API Not Working
- Verify all environment variables are set in Vercel (not just `.env` file)
- Check Vercel function logs for errors

### Voice Recognition Not Working
- Voice features only work on HTTPS (Vercel provides this automatically)
- Allow microphone permissions in browser

## 📝 Post-Deployment Security

**CRITICAL**: The following API keys were exposed in conversation and must be regenerated:

1. **Groq API Key**: Go to console.groq.com → API Keys → Regenerate
2. **Google OAuth**: Consider rotating client secret if concerned
3. Update all keys in Vercel environment variables
4. Redeploy

## 🎯 Next Steps

1. Test the application thoroughly on the live URL
2. Share the URL with others to test
3. Monitor Vercel logs for any errors
4. Consider adding custom domain (optional)

## 📚 Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- [Google Calendar API](https://developers.google.com/calendar)
- [Groq Documentation](https://console.groq.com/docs)
