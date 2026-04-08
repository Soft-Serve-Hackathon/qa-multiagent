#!/usr/bin/env python3
"""
Load Test: Simulating 50 concurrent incidents.

Validates system behavior under load:
- Throughput: incidents/second
- Latency: response time per incident
- Success rate: % of successful creations
- Distribution: severity/module breakdown

Usage:
  # Mock mode (fast, no credentials)
  python load_test_50_incidents.py --mock --incidents 50
  
  # Real mode (with real Trello)
  python load_test_50_incidents.py --real --incidents 50
  
  # Custom count
  python load_test_50_incidents.py --mock --incidents 100
"""

import asyncio
import time
import json
import sys
from typing import List, Optional
from datetime import datetime
import httpx
import click

BASE_URL = "http://localhost:8000/api"

# Realistic incident templates
INCIDENT_TEMPLATES = [
    {
        "title": "Database connection pool exhausted",
        "description": "Current pool usage: 95/100 connections. New requests timing out. Last occurred 2 days ago.",
    },
    {
        "title": "API Gateway memory leak detected",
        "description": "Memory increasing ~5% per hour. Current: 3.2GB/4GB. At this rate, will OOM in ~4 hours. Check recent deployments.",
    },
    {
        "title": "Cache invalidation performing slowly",
        "description": "Redis commands taking 100-500ms. Usually <10ms. Page loads affected. Possible network issue?",
    },
    {
        "title": "Authentication service 503 errors",
        "description": "JWT validation failing intermittently. Error rate: ~10%. Users reporting login issues in batches.",
    },
    {
        "title": "Elasticsearch cluster health YELLOW",
        "description": "1 shard unassigned. Search results may be incomplete. Need to investigate shard allocation.",
    },
    {
        "title": "Nginx worker processes high CPU",
        "description": "Upstream backend latency spiked. Worker processes hitting 100% CPU. Possible DDoS or traffic surge.",
    },
    {
        "title": "S3 upload failures (403 Forbidden)",
        "description": "User file uploads failing with 403. IAM policy or credentials issue? Check AWS console.",
    },
    {
        "title": "Message queue depth increasing",
        "description": "RabbitMQ queue backlog growing. No messages being consumed? Consumer process down?",
    },
    {
        "title": "SSL certificate expiring soon",
        "description": "Production cert expires in 7 days. Need to renew before incident occurs.",
    },
    {
        "title": "Database replication lag critical",
        "description": "Read replicas falling behind write master by >30 seconds. Could cause stale data issues.",
    },
]


class LoadTestMetrics:
    """Collect and analyze load test metrics."""
    
    def __init__(self):
        self.submit_times = []
        self.status_check_times = []
        self.errors: List[dict] = []
        self.trace_ids: List[str] = []
        self.startup_time = time.monotonic()
    
    def add_submit_time(self, ms: int):
        self.submit_times.append(ms)
    
    def add_status_time(self, ms: int):
        self.status_check_times.append(ms)
    
    def add_error(self, incident_idx: int, error: str):
        self.errors.append({"incident": incident_idx, "error": error})
    
    def add_trace_id(self, trace_id: str):
        self.trace_ids.append(trace_id)
    
    def summary(self) -> dict:
        """Generate summary statistics."""
        if not self.submit_times:
            return {}
        
        return {
            "total_incidents": len(self.submit_times),
            "successful": len(self.submit_times),
            "failed": len(self.errors),
            "success_rate": f"{(len(self.submit_times) / (len(self.submit_times) + len(self.errors)) * 100):.1f}%",
            "submit_times": {
                "min_ms": min(self.submit_times),
                "max_ms": max(self.submit_times),
                "avg_ms": sum(self.submit_times) / len(self.submit_times),
                "p95_ms": sorted(self.submit_times)[int(len(self.submit_times) * 0.95)],
                "p99_ms": sorted(self.submit_times)[int(len(self.submit_times) * 0.99)],
            },
            "throughput_incidents_per_sec": len(self.submit_times) / max(
                (time.monotonic() - self.startup_time), 1
            ),
        }


class LoadTestRunner:
    """Execute load test with concurrent incident submissions."""
    
    def __init__(self, mock_mode: bool = True, verbose: bool = False):
        self.mock_mode = mock_mode
        self.base_url = BASE_URL
        self.verbose = verbose
        self.metrics = LoadTestMetrics()
    
    async def submit_incident(
        self,
        session: httpx.AsyncClient,
        incident_idx: int,
    ) -> Optional[str]:
        """Submit single incident, return trace_id on success."""
        template_idx = incident_idx % len(INCIDENT_TEMPLATES)
        template = INCIDENT_TEMPLATES[template_idx]
        
        # Vary the title slightly for each incident
        title = f"{template['title']} [{incident_idx:03d}]"
        
        files = {
            "title": (None, title),
            "description": (None, template["description"]),
            "reporter_email": (None, f"test{incident_idx}@company.com"),
        }
        
        start = time.monotonic()
        try:
            response = await session.post(
                f"{self.base_url}/incidents",
                files=files,
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            
            if response.status_code == 201:
                data = response.json()
                trace_id = data.get("trace_id")
                
                self.metrics.add_submit_time(duration_ms)
                self.metrics.add_trace_id(trace_id)
                
                if self.verbose:
                    click.echo(f"  [{incident_idx}] ✅ {duration_ms}ms → {trace_id[:8]}...")
                
                return trace_id
            else:
                error = f"HTTP {response.status_code}: {response.text[:100]}"
                self.metrics.add_error(incident_idx, error)
                if self.verbose:
                    click.echo(f"  [{incident_idx}] ❌ {error}")
                return None
        
        except Exception as e:
            error = str(e)
            self.metrics.add_error(incident_idx, error)
            if self.verbose:
                click.echo(f"  [{incident_idx}] ❌ {error}")
            return None
    
    async def check_status(
        self,
        session: httpx.AsyncClient,
        trace_id: str,
    ) -> dict:
        """Check ticket creation status."""
        start = time.monotonic()
        try:
            response = await session.get(f"{self.base_url}/incidents/{trace_id}")
            duration_ms = int((time.monotonic() - start) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.metrics.add_status_time(duration_ms)
                
                return {
                    "trace_id": trace_id,
                    "status": data.get("status"),
                    "has_ticket": bool(data.get("ticket_id")),
                    "severity": data.get("severity"),
                }
            return {"trace_id": trace_id, "status": "not_found"}
        
        except Exception as e:
            return {"trace_id": trace_id, "error": str(e)}
    
    async def run_load_test(self, num_incidents: int = 50, timeout_seconds: int = 60):
        """Run concurrent load test."""
        click.echo(f"\n{'='*70}")
        click.echo(f"🚀 LOAD TEST: {num_incidents} Concurrent Incidents")
        click.echo(f"⏰ Started: {datetime.now().isoformat()}")
        click.echo(f"🔧 Mode: {'MOCK' if self.mock_mode else 'REAL'}")
        click.echo(f"💾 Timeout: {timeout_seconds}s")
        click.echo(f"{'='*70}\n")
        
        # ─────────────────────────────────────────────────────────────
        # PHASE 1: Submit all incidents concurrently
        # ─────────────────────────────────────────────────────────────
        
        click.echo(f"📝 PHASE 1: Submitting {num_incidents} incidents concurrently...")
        
        async with httpx.AsyncClient(timeout=timeout_seconds) as session:
            tasks = [
                self.submit_incident(session, i)
                for i in range(num_incidents)
            ]
            
            start_submit = time.monotonic()
            trace_ids = await asyncio.gather(*tasks, return_exceptions=False)
            duration_submit = time.monotonic() - start_submit
        
        successful_ids = [t for t in trace_ids if t is not None]
        failed_count = num_incidents - len(successful_ids)
        
        click.echo(f"✅ Submitted: {len(successful_ids)}/{num_incidents}")
        if failed_count > 0:
            click.echo(f"❌ Failed: {failed_count}")
        click.echo(f"⏱️  Duration: {duration_submit:.2f}s")
        click.echo(f"📊 Throughput: {len(successful_ids)/duration_submit:.1f} incidents/sec\n")
        
        if len(successful_ids) == 0:
            click.echo("❌ No incidents submitted successfully. Aborting.")
            return
        
        # ─────────────────────────────────────────────────────────────
        # PHASE 2: Poll for ticket creation
        # ─────────────────────────────────────────────────────────────
        
        click.echo(f"🎫 PHASE 2: Polling for ticket creation (up to {timeout_seconds}s)...")
        
        max_polls = timeout_seconds
        last_count = 0
        
        for poll_num in range(1, max_polls + 1):
            async with httpx.AsyncClient(timeout=timeout_seconds) as session:
                tasks = [
                    self.check_status(session, trace_id)
                    for trace_id in successful_ids
                ]
                status_results = await asyncio.gather(*tasks, return_exceptions=False)
            
            tickets_created = len([
                r for r in status_results
                if r.get("has_ticket") is True
            ])
            
            # Show progress
            if tickets_created > last_count:
                click.echo(f"  Poll {poll_num:2d}/{max_polls}: {tickets_created}/{len(successful_ids)} tickets ✓")
                last_count = tickets_created
            else:
                click.echo(f"  Poll {poll_num:2d}/{max_polls}: {tickets_created}/{len(successful_ids)} tickets")
            
            if tickets_created == len(successful_ids):
                click.echo("✅ All tickets created!")
                break
            
            await asyncio.sleep(1)
        
        # ─────────────────────────────────────────────────────────────
        # PHASE 3: Analysis
        # ─────────────────────────────────────────────────────────────
        
        click.echo(f"\n{'='*70}")
        click.echo("📊 RESULTS & ANALYSIS")
        click.echo(f"{'='*70}\n")
        
        # Severity distribution
        severity_dist = {}
        for r in status_results:
            sev = r.get("severity", "unknown")
            severity_dist[sev] = severity_dist.get(sev, 0) + 1
        
        click.echo("Severity Distribution:")
        for sev in sorted(severity_dist.keys()):
            count = severity_dist[sev]
            pct = (count / len(status_results) * 100)
            click.echo(f"  {sev:3s}: {count:2d} incidents ({pct:5.1f}%)")
        
        click.echo()
        click.echo("Performance Metrics:")
        
        summary = self.metrics.summary()
        if "submit_times" in summary:
            st = summary["submit_times"]
            click.echo(f"  Submit latency:")
            click.echo(f"    Min:  {st['min_ms']:4d}ms")
            click.echo(f"    Avg:  {st['avg_ms']:4.0f}ms")
            click.echo(f"    P95:  {st['p95_ms']:4d}ms")
            click.echo(f"    P99:  {st['p99_ms']:4d}ms")
            click.echo(f"    Max:  {st['max_ms']:4d}ms")
            click.echo(f"  Throughput: {summary['throughput_incidents_per_sec']:.1f} incidents/sec")
            click.echo(f"  Success rate: {summary['success_rate']}")
        
        click.echo()
        click.echo("✅ Load test completed!")
        
        return {
            "mode": "MOCK" if self.mock_mode else "REAL",
            "total_incidents": len(successful_ids),
            "statistics": summary,
            "severity_distribution": severity_dist,
            "completed_at": datetime.now().isoformat(),
        }


@click.command()
@click.option("--mock", "mock_mode", is_flag=True, default=True, help="Use mock mode (default)")
@click.option("--real", "mock_mode", flag_value=False, help="Use real integrations")
@click.option("--incidents", "-n", default=50, type=int, help="Number of concurrent incidents (default: 50)")
@click.option("--timeout", "-t", default=60, type=int, help="Timeout in seconds (default: 60)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(mock_mode: bool, incidents: int, timeout: int, verbose: bool):
    """Load test: Submit N concurrent incidents and measure system behavior."""
    
    # Validate
    if incidents < 1 or incidents > 1000:
        click.echo("❌ Incidents must be between 1 and 1000")
        sys.exit(1)
    
    # Run test
    runner = LoadTestRunner(mock_mode=mock_mode, verbose=verbose)
    result = asyncio.run(runner.run_load_test(num_incidents=incidents, timeout_seconds=timeout))
    
    # Save results
    if result:
        with open(f"load_test_results_{datetime.now().isoformat()}.json", "w") as f:
            json.dump(result, f, indent=2)
        click.echo(f"\n📁 Results saved to load_test_results_*.json")


if __name__ == "__main__":
    main()
