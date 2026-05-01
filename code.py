import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------
# 1. NETWORK BUILDER (High-Contrast Capacity)
# ---------------------------------------------------------

def create_supply_chain(style='lean'):
    G = nx.DiGraph()
    if style == 'lean':
        # LEAN: Exactly matches your values. No safety margin.
        edges = [
            ('S1', 'DC1', 25, 50), ('S2', 'DC2', 25, 50),
            ('DC1', 'Z1', 20, 30), ('DC1', 'Z2', 10, 30),
            ('DC2', 'Z3', 40, 30)
        ]
    else:
        # ROBUST: High redundancy + High Backup Capacity
        # We give S1-DC2 enough capacity to actually 'rescue' S1's supply.
        edges = [
            ('S1', 'DC1', 25, 50), ('S1', 'DC2', 60, 45), # Strategic Backup
            ('S2', 'DC1', 10, 40), ('S2', 'DC2', 25, 50),
            ('DC1', 'Z1', 20, 30), ('DC1', 'Z2', 10, 30), ('DC1', 'Z3', 5, 20),
            ('DC2', 'Z1', 20, 25), ('DC2', 'Z2', 10, 25), ('DC2', 'Z3', 40, 30)
        ]
    
    for u, v, cap, cost in edges:
        G.add_edge(u, v, capacity=cap, fixed_cost=cost)
    return G

# ---------------------------------------------------------
# 2. ANALYSIS ENGINE
# ---------------------------------------------------------

def calculate_max_service(G):
    if G.number_of_nodes() == 0: return 0
    H = G.copy()
    sources = [s for s in ['S1', 'S2'] if s in G.nodes()]
    sinks = [z for z in ['Z1', 'Z2', 'Z3'] if z in G.nodes()]
    if not sources or not sinks: return 0
    
    for s in sources: H.add_edge('SRC', s, capacity=999)
    for z in sinks: H.add_edge(z, 'SNK', capacity=999)
    flow, _ = nx.maximum_flow(H, 'SRC', 'SNK')
    return flow

def analyze_network(G, name):
    # Performance Metrics
    fixed_cost = sum(d['fixed_cost'] for u, v, d in G.edges(data=True))
    base_flow = calculate_max_service(G)
    
    # Centrality
    in_c = nx.in_degree_centrality(G)
    out_c = nx.out_degree_centrality(G)
    bet_c = nx.betweenness_centrality(G)
    
    # Disruption Simulation (Targeting DC1)
    G_broken = G.copy()
    if 'DC1' in G_broken:
        G_broken.remove_node('DC1')
    post_flow = calculate_max_service(G_broken)
    
    resilience = (post_flow / base_flow * 100) if base_flow > 0 else 0
    
    return {
        "Data": {"Network": name, "Fixed Cost": f"${fixed_cost}", "Max Capacity": base_flow, 
                 "Post-Failure Cap": post_flow, "Resilience %": f"{resilience:.1f}%"},
        "Centrality": (in_c, out_c, bet_c)
    }

# ---------------------------------------------------------
# 3. EXECUTION & OUTPUT
# ---------------------------------------------------------

lean_results = analyze_network(create_supply_chain('lean'), "Lean")
robust_results = analyze_network(create_supply_chain('robust'), "Robust")

# PRINT TERMINAL OUTPUT
for res in [lean_results, robust_results]:
    print(f"\nCentrality Analysis ({res['Data']['Network']}):")
    in_c, out_c, bet_c = res['Centrality']
    for node in sorted(in_c.keys()):
        print(f"{node}: In={in_c[node]:.3f}, Out={out_c[node]:.3f}, Bet={bet_c[node]:.3f}")

print(f"\nDisrupting Critical Node: DC1")

print("\n--- COMPARATIVE ANALYSIS ---")
comparison_df = pd.DataFrame([lean_results['Data'], robust_results['Data']])
print(comparison_df.to_string(index=False))

# VISUALIZATION
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
pos = {'S1':(0,2), 'S2':(0,0), 'DC1':(1,2), 'DC2':(1,0), 'Z1':(2,2), 'Z2':(2,1), 'Z3':(2,0)}

def draw_network(style, results, ax):
    G = create_supply_chain(style)
    nx.draw(G, pos, ax=ax, with_labels=True, node_size=2200, 
            node_color='orange' if style == 'lean' else 'skyblue',
            font_weight='bold', arrowsize=20)
    labels = nx.get_edge_attributes(G, 'capacity')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, ax=ax)
    ax.set_title(f"{results['Data']['Network']} Design\nResilience: {results['Data']['Resilience %']}", fontsize=14)

draw_network('lean', lean_results, ax1)
draw_network('robust', robust_results, ax2)
plt.tight_layout()
plt.show()