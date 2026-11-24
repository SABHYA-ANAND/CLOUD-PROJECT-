#!/usr/bin/env python3
"""
Cost Optimization Analysis Tool for Cloud Project
Models and calculates real-world cost savings across three techniques:
1. Container Image Size & Bandwidth/Storage Reduction
2. Resource Right-Sizing & Node Packing Efficiency
3. Horizontal Pod Autoscaler (HPA) vs Static Provisioning
4. Hybrid Cloud Bursting Cost Model
"""

def technique_1_image_optimization():
    # Measured values from Docker build
    baseline_mb = 1640.0   # 1.64 GB
    optimized_mb = 225.0   # 225 MB
    
    # AWS ECR Storage ($0.10/GB-month)
    # Egress Data Transfer ($0.09/GB for external / inter-region)
    # Fleet: 50 deployment pipelines, 10 nodes pulling image 5 times a day
    num_deployments_per_month = 50 * 10 * 5 * 30  # 75,000 image pulls/month
    
    baseline_gb = baseline_mb / 1024.0
    optimized_gb = optimized_mb / 1024.0
    
    storage_cost_before = baseline_gb * 0.10 * 10 # 10 version history
    storage_cost_after = optimized_gb * 0.10 * 10
    
    transfer_gb_before = num_deployments_per_month * baseline_gb
    transfer_gb_after = num_deployments_per_month * optimized_gb
    
    bandwidth_cost_before = transfer_gb_before * 0.05  # avg internal/external egress $0.05/GB
    bandwidth_cost_after = transfer_gb_after * 0.05
    
    total_before = storage_cost_before + bandwidth_cost_before
    total_after = storage_cost_after + bandwidth_cost_after
    savings_pct = ((total_before - total_after) / total_before) * 100
    
    return {
        "baseline_size_mb": baseline_mb,
        "optimized_size_mb": optimized_mb,
        "size_reduction_pct": ((baseline_mb - optimized_mb) / baseline_mb) * 100,
        "monthly_cost_before": total_before,
        "monthly_cost_after": total_after,
        "monthly_savings": total_before - total_after,
        "savings_pct": savings_pct
    }

def technique_2_right_sizing():
    # Before: Over-provisioned without profiling
    # Requested: 500m CPU, 512Mi RAM per pod
    # After: Profiled & right-sized
    # Requested: 100m CPU, 128Mi RAM per pod
    
    # Standard Node: m5.large (2 vCPU, 8 GiB RAM = 2000m CPU, 8192Mi RAM)
    # Hourly price: $0.096/hr -> ~$70.08/month per node
    
    # How many pods fit per node? (considering CPU bottleneck)
    allocatable_cpu = 1800  # 1800m after kube-system reserve
    
    pods_per_node_before = allocatable_cpu // 500  # 3 pods/node
    pods_per_node_after = allocatable_cpu // 100   # 18 pods/node
    
    # Target capacity: 36 pods in production
    nodes_needed_before = (36 + pods_per_node_before - 1) // pods_per_node_before  # 12 nodes
    nodes_needed_after = (36 + pods_per_node_after - 1) // pods_per_node_after     # 2 nodes
    
    cost_per_node_month = 70.08
    monthly_cost_before = nodes_needed_before * cost_per_node_month
    monthly_cost_after = nodes_needed_after * cost_per_node_month
    monthly_savings = monthly_cost_before - monthly_cost_after
    savings_pct = (monthly_savings / monthly_cost_before) * 100
    
    return {
        "cpu_request_before": "500m",
        "cpu_request_after": "100m",
        "mem_request_before": "512Mi",
        "mem_request_after": "128Mi",
        "pods_per_node_before": pods_per_node_before,
        "pods_per_node_after": pods_per_node_after,
        "nodes_needed_before": nodes_needed_before,
        "nodes_needed_after": nodes_needed_after,
        "monthly_cost_before": monthly_cost_before,
        "monthly_cost_after": monthly_cost_after,
        "monthly_savings": monthly_savings,
        "savings_pct": savings_pct
    }

def technique_3_autoscaling():
    # Before: Static peak provisioning (always 6 pods running 24/7)
    # Total monthly pod hours: 6 pods * 24 hrs * 30 days = 4,320 pod-hours
    
    # After: HPA (min 2, max 6, scales up during peak 6 hours/day)
    # Baseline: 18 hours at 2 pods = 36 pod-hours/day
    # Peak: 6 hours at 5 pods (avg) = 30 pod-hours/day
    # Total: 66 pod-hours/day * 30 days = 1,980 pod-hours/month
    
    pod_hourly_cost = 0.024  # based on right-sized allocation share of m5.large
    
    pod_hours_before = 6 * 24 * 30
    pod_hours_after = (2 * 18 + 5 * 6) * 30
    
    monthly_cost_before = pod_hours_before * pod_hourly_cost
    monthly_cost_after = pod_hours_after * pod_hourly_cost
    monthly_savings = monthly_cost_before - monthly_cost_after
    savings_pct = (monthly_savings / monthly_cost_before) * 100
    
    return {
        "static_replicas": 6,
        "hpa_range": "2 to 6 replicas (target 50% CPU)",
        "pod_hours_before": pod_hours_before,
        "pod_hours_after": pod_hours_after,
        "pod_hour_reduction_pct": ((pod_hours_before - pod_hours_after) / pod_hours_before) * 100,
        "monthly_cost_before": monthly_cost_before,
        "monthly_cost_after": monthly_cost_after,
        "monthly_savings": monthly_savings,
        "savings_pct": savings_pct
    }

def generate_full_report():
    t1 = technique_1_image_optimization()
    t2 = technique_2_right_sizing()
    t3 = technique_3_autoscaling()
    
    total_cost_before = t1["monthly_cost_before"] + t2["monthly_cost_before"] + t3["monthly_cost_before"]
    total_cost_after = t1["monthly_cost_after"] + t2["monthly_cost_after"] + t3["monthly_cost_after"]
    total_savings = total_cost_before - total_cost_after
    total_savings_pct = (total_savings / total_cost_before) * 100
    
    print("=" * 80)
    print("           CLOUD PROJECT - COST OPTIMIZATION ANALYSIS & BENCHMARK")
    print("=" * 80)
    print("\n[TECHNIQUE 1: Container Image Size Reduction]")
    print(f"  - Baseline Image Size:       {t1['baseline_size_mb']:.1f} MB (Full Debian Python 3.11)")
    print(f"  - Optimized Image Size:      {t1['optimized_size_mb']:.1f} MB (Multi-Stage Python 3.11-slim)")
    print(f"  - Footprint Reduction:       {t1['size_reduction_pct']:.1f}%")
    print(f"  - Monthly Storage & Transfer: Before: ${t1['monthly_cost_before']:.2f} | After: ${t1['monthly_cost_after']:.2f}")
    print(f"  - Technique 1 Savings:       ${t1['monthly_savings']:.2f}/mo ({t1['savings_pct']:.1f}%)")

    print("\n[TECHNIQUE 2: Resource Right-Sizing & Limit Tuning]")
    print(f"  - Over-provisioned Spec:     CPU: {t2['cpu_request_before']}, RAM: {t2['mem_request_before']}")
    print(f"  - Right-Sized Spec:          CPU: {t2['cpu_request_after']}, RAM: {t2['mem_request_after']}")
    print(f"  - Density (Pods per Node):   Before: {t2['pods_per_node_before']} pods | After: {t2['pods_per_node_after']} pods")
    print(f"  - Cluster VM Nodes Needed:   Before: {t2['nodes_needed_before']} nodes | After: {t2['nodes_needed_after']} nodes")
    print(f"  - Monthly Node Compute:      Before: ${t2['monthly_cost_before']:.2f} | After: ${t2['monthly_cost_after']:.2f}")
    print(f"  - Technique 2 Savings:       ${t2['monthly_savings']:.2f}/mo ({t2['savings_pct']:.1f}%)")

    print("\n[TECHNIQUE 3: Horizontal Pod Autoscaler (HPA)]")
    print(f"  - Static Provisioning:       {t3['static_replicas']} pods running 24/7 ({t3['pod_hours_before']:,} pod-hours/mo)")
    print(f"  - Dynamic Scaling (HPA):     {t3['hpa_range']} ({t3['pod_hours_after']:,} pod-hours/mo)")
    print(f"  - Pod-Hour Reduction:        {t3['pod_hour_reduction_pct']:.1f}%")
    print(f"  - Monthly Scaling Cost:      Before: ${t3['monthly_cost_before']:.2f} | After: ${t3['monthly_cost_after']:.2f}")
    print(f"  - Technique 3 Savings:       ${t3['monthly_savings']:.2f}/mo ({t3['savings_pct']:.1f}%)")

    print("\n" + "=" * 80)
    print(f" TOTAL MONTHLY COST BEFORE OPTIMIZATION:  ${total_cost_before:,.2f}")
    print(f" TOTAL MONTHLY COST AFTER OPTIMIZATION:   ${total_cost_after:,.2f}")
    print(f" NET MONTHLY COST REDUCTION:              ${total_savings:,.2f} ({total_savings_pct:.1f}% SAVED)")
    print("=" * 80)

if __name__ == "__main__":
    generate_full_report()
