"""
Analytics routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..models import StandardResponse, EmailStats, EmailAnalytics
from core.security import verify_api_key
from core.database import database_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/overview", response_model=StandardResponse)
async def get_analytics_overview(
    days: int = Query(7, le=365),
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get analytics overview
    
    Get high-level analytics for the specified period.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get email logs for the period
        logs = await database_manager.get_email_logs(
            limit=10000,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate basic metrics
        total_emails = len(logs)
        received_emails = len([log for log in logs if log.get('action') == 'received'])
        auto_replies = len([log for log in logs if log.get('action') == 'auto_replied'])
        manual_replies = len([log for log in logs if log.get('action') == 'replied'])
        failed_emails = len([log for log in logs if log.get('status') == 'failed'])
        
        success_rate = ((auto_replies + manual_replies) / received_emails * 100) if received_emails > 0 else 0
        
        # Calculate daily breakdown
        daily_stats = {}
        for log in logs:
            created_at = log.get('created_at')
            if isinstance(created_at, str):
                date_key = created_at[:10]  # YYYY-MM-DD
            else:
                date_key = created_at.strftime('%Y-%m-%d')
            
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'received': 0,
                    'auto_replied': 0,
                    'manual_replied': 0,
                    'failed': 0
                }
            
            action = log.get('action', '')
            if action == 'received':
                daily_stats[date_key]['received'] += 1
            elif action == 'auto_replied':
                daily_stats[date_key]['auto_replied'] += 1
            elif action == 'replied':
                daily_stats[date_key]['manual_replied'] += 1
            elif log.get('status') == 'failed':
                daily_stats[date_key]['failed'] += 1
        
        # Top domains by email volume
        domain_stats = {}
        for log in logs:
            sender = log.get('sender', '')
            if '@' in sender:
                domain = sender.split('@')[-1].lower()
                domain_stats[domain] = domain_stats.get(domain, 0) + 1
        
        top_domains = sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        overview = {
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_emails": total_emails,
                "received_emails": received_emails,
                "auto_replies": auto_replies,
                "manual_replies": manual_replies,
                "total_replies": auto_replies + manual_replies,
                "failed_emails": failed_emails,
                "success_rate": round(success_rate, 2)
            },
            "daily_breakdown": [
                {
                    "date": date,
                    "stats": stats
                }
                for date, stats in sorted(daily_stats.items())
            ],
            "top_domains": [
                {"domain": domain, "email_count": count}
                for domain, count in top_domains
            ]
        }
        
        return StandardResponse(
            success=True,
            message=f"Analytics overview for last {days} days",
            data=overview
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily", response_model=List[EmailAnalytics])
async def get_daily_analytics(
    days: int = Query(30, le=365),
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get daily analytics breakdown
    
    Get detailed day-by-day analytics for the specified period.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get email logs for the period
        logs = await database_manager.get_email_logs(
            limit=10000,
            start_date=start_date,
            end_date=end_date
        )
        
        # Group by date
        daily_data = {}
        for log in logs:
            created_at = log.get('created_at')
            if isinstance(created_at, str):
                date_key = created_at[:10]
            else:
                date_key = created_at.strftime('%Y-%m-%d')
            
            if date_key not in daily_data:
                daily_data[date_key] = []
            daily_data[date_key].append(log)
        
        # Calculate daily stats
        analytics = []
        for date_str in sorted(daily_data.keys()):
            day_logs = daily_data[date_str]
            
            total_emails = len(day_logs)
            auto_replies = len([log for log in day_logs if log.get('action') == 'auto_replied'])
            manual_replies = len([log for log in day_logs if log.get('action') == 'replied'])
            failed_emails = len([log for log in day_logs if log.get('status') == 'failed'])
            
            success_rate = ((auto_replies + manual_replies) / total_emails * 100) if total_emails > 0 else 0
            
            stats = EmailStats(
                total_emails=total_emails,
                replies_sent=auto_replies + manual_replies,
                auto_replies=auto_replies,
                manual_replies=manual_replies,
                failed_emails=failed_emails,
                success_rate=round(success_rate, 2)
            )
            
            analytics.append(EmailAnalytics(
                date=date_str,
                stats=stats
            ))
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting daily analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains", response_model=StandardResponse)
async def get_domain_analytics(
    days: int = Query(30, le=365),
    limit: int = Query(20, le=100),
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get domain-based analytics
    
    Get analytics broken down by email domains.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get email logs for the period
        logs = await database_manager.get_email_logs(
            limit=10000,
            start_date=start_date,
            end_date=end_date
        )
        
        # Group by domain
        domain_data = {}
        for log in logs:
            sender = log.get('sender', '')
            if '@' in sender:
                domain = sender.split('@')[-1].lower()
                
                if domain not in domain_data:
                    domain_data[domain] = []
                domain_data[domain].append(log)
        
        # Calculate domain stats
        domain_analytics = []
        for domain, domain_logs in domain_data.items():
            total_emails = len(domain_logs)
            received_emails = len([log for log in domain_logs if log.get('action') == 'received'])
            auto_replies = len([log for log in domain_logs if log.get('action') == 'auto_replied'])
            manual_replies = len([log for log in domain_logs if log.get('action') == 'replied'])
            failed_emails = len([log for log in domain_logs if log.get('status') == 'failed'])
            
            reply_rate = ((auto_replies + manual_replies) / received_emails * 100) if received_emails > 0 else 0
            
            domain_analytics.append({
                "domain": domain,
                "total_emails": total_emails,
                "received_emails": received_emails,
                "auto_replies": auto_replies,
                "manual_replies": manual_replies,
                "total_replies": auto_replies + manual_replies,
                "failed_emails": failed_emails,
                "reply_rate": round(reply_rate, 2)
            })
        
        # Sort by total emails and limit
        domain_analytics.sort(key=lambda x: x['total_emails'], reverse=True)
        domain_analytics = domain_analytics[:limit]
        
        return StandardResponse(
            success=True,
            message=f"Domain analytics for last {days} days",
            data={
                "domains": domain_analytics,
                "period_days": days,
                "total_domains": len(domain_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting domain analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance", response_model=StandardResponse)
async def get_performance_analytics(
    days: int = Query(7, le=365),
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get performance analytics
    
    Get performance metrics and trends.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get email logs for the period
        logs = await database_manager.get_email_logs(
            limit=10000,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate hourly distribution
        hourly_distribution = {}
        for log in logs:
            created_at = log.get('created_at')
            if isinstance(created_at, str):
                hour = int(created_at[11:13])  # Extract hour from ISO string
            else:
                hour = created_at.hour
            
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        # Calculate response times (simplified - would need more detailed tracking in production)
        avg_response_time = "< 1 minute"  # Placeholder
        
        # Calculate trends (compare with previous period)
        prev_start_date = start_date - timedelta(days=days)
        prev_logs = await database_manager.get_email_logs(
            limit=10000,
            start_date=prev_start_date,
            end_date=start_date
        )
        
        current_period_count = len(logs)
        previous_period_count = len(prev_logs)
        
        trend_percentage = 0
        if previous_period_count > 0:
            trend_percentage = ((current_period_count - previous_period_count) / previous_period_count) * 100
        
        performance = {
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": {
                "avg_response_time": avg_response_time,
                "total_emails_processed": current_period_count,
                "trend_percentage": round(trend_percentage, 2),
                "trend_direction": "up" if trend_percentage > 0 else "down" if trend_percentage < 0 else "stable"
            },
            "hourly_distribution": [
                {"hour": hour, "email_count": count}
                for hour, count in sorted(hourly_distribution.items())
            ],
            "comparison": {
                "current_period": current_period_count,
                "previous_period": previous_period_count,
                "change": current_period_count - previous_period_count
            }
        }
        
        return StandardResponse(
            success=True,
            message=f"Performance analytics for last {days} days",
            data=performance
        )
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export", response_model=StandardResponse)
async def export_analytics(
    days: int = Query(30, le=365),
    format: str = Query("json", regex="^(json|csv)$"),
    auth_data: dict = Depends(verify_api_key)
):
    """
    Export analytics data
    
    Export analytics data in JSON or CSV format.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get email logs for the period
        logs = await database_manager.get_email_logs(
            limit=10000,
            start_date=start_date,
            end_date=end_date
        )
        
        if format.lower() == "csv":
            # Convert to CSV format (simplified)
            csv_data = "date,sender,recipient,subject,action,status\n"
            for log in logs:
                csv_data += f"{log.get('created_at', '')},{log.get('sender', '')},{log.get('recipient', '')},{log.get('subject', '')},{log.get('action', '')},{log.get('status', '')}\n"
            
            return StandardResponse(
                success=True,
                message=f"Analytics data exported as CSV ({len(logs)} records)",
                data={
                    "format": "csv",
                    "content": csv_data,
                    "record_count": len(logs)
                }
            )
        else:
            # Return as JSON
            return StandardResponse(
                success=True,
                message=f"Analytics data exported as JSON ({len(logs)} records)",
                data={
                    "format": "json",
                    "records": logs,
                    "record_count": len(logs),
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "days": days
                    }
                }
            )
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
