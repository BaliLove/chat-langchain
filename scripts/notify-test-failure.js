#!/usr/bin/env node

/**
 * Notification script for test failures
 * Supports Slack, Discord, and email notifications
 */

const https = require('https');

class TestNotifier {
  constructor() {
    // Load from environment variables
    this.slackWebhook = process.env.SLACK_WEBHOOK_URL;
    this.discordWebhook = process.env.DISCORD_WEBHOOK_URL;
    this.emailConfig = {
      enabled: process.env.EMAIL_NOTIFICATIONS === 'true',
      to: process.env.NOTIFICATION_EMAIL
    };
  }

  async notify(data) {
    const { type, title, description, url, severity = 'medium' } = data;
    
    const promises = [];
    
    if (this.slackWebhook) {
      promises.push(this.notifySlack(data));
    }
    
    if (this.discordWebhook) {
      promises.push(this.notifyDiscord(data));
    }
    
    if (this.emailConfig.enabled) {
      promises.push(this.notifyEmail(data));
    }
    
    await Promise.allSettled(promises);
  }

  async notifySlack(data) {
    const color = this.getSeverityColor(data.severity);
    
    const payload = {
      attachments: [{
        color,
        title: data.title,
        text: data.description,
        fields: [
          {
            title: 'Type',
            value: data.type,
            short: true
          },
          {
            title: 'Severity',
            value: data.severity,
            short: true
          }
        ],
        actions: data.url ? [{
          type: 'button',
          text: 'View Details',
          url: data.url
        }] : []
      }]
    };

    return this.sendWebhook(this.slackWebhook, payload);
  }

  async notifyDiscord(data) {
    const color = parseInt(this.getSeverityColor(data.severity).replace('#', ''), 16);
    
    const payload = {
      embeds: [{
        title: data.title,
        description: data.description,
        color,
        fields: [
          {
            name: 'Type',
            value: data.type,
            inline: true
          },
          {
            name: 'Severity',
            value: data.severity,
            inline: true
          }
        ],
        url: data.url
      }]
    };

    return this.sendWebhook(this.discordWebhook, payload);
  }

  async notifyEmail(data) {
    // This would integrate with your email service
    console.log('Email notification:', data);
    // Implementation depends on your email service (SendGrid, AWS SES, etc.)
  }

  async sendWebhook(url, payload) {
    return new Promise((resolve, reject) => {
      const data = JSON.stringify(payload);
      const urlObj = new URL(url);
      
      const options = {
        hostname: urlObj.hostname,
        port: 443,
        path: urlObj.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': data.length
        }
      };

      const req = https.request(options, (res) => {
        if (res.statusCode < 300) {
          resolve();
        } else {
          reject(new Error(`Webhook failed: ${res.statusCode}`));
        }
      });

      req.on('error', reject);
      req.write(data);
      req.end();
    });
  }

  getSeverityColor(severity) {
    const colors = {
      low: '#36a64f',
      medium: '#ff9f1a',
      high: '#e01e5a',
      critical: '#b00020'
    };
    return colors[severity] || colors.medium;
  }
}

// Parse GitHub Actions context if available
function parseGitHubContext() {
  if (process.env.GITHUB_ACTIONS) {
    return {
      type: 'ci-failure',
      title: `CI Failed: ${process.env.GITHUB_WORKFLOW}`,
      description: `Failed on ${process.env.GITHUB_REF} at ${process.env.GITHUB_SHA}`,
      url: `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`,
      severity: 'high'
    };
  }
  return null;
}

// Main execution
if (require.main === module) {
  const notifier = new TestNotifier();
  
  // Get notification data from arguments or GitHub context
  const data = process.argv[2] ? JSON.parse(process.argv[2]) : parseGitHubContext();
  
  if (data) {
    notifier.notify(data).catch(console.error);
  } else {
    console.log('No notification data provided');
  }
}

module.exports = TestNotifier;