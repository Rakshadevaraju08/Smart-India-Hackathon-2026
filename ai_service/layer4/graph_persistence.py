import pickle
import os
import networkx as nx
from typing import Optional

def save_graph(G: nx.MultiDiGraph, path: str):
    """
    Saves the NetworkX MultiDiGraph to a binary file using pickle.
    Preserves all graph, node, and edge attributes.
    """
    if not isinstance(G, nx.MultiDiGraph):
        raise TypeError(f"Expected a NetworkX MultiDiGraph, got {type(G)}")
        
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    
    with open(path, "wb") as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_graph(path: str) -> nx.MultiDiGraph:
    """
    Loads the NetworkX MultiDiGraph from a binary pickle file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Graph file not found at {path}")
        
    with open(path, "rb") as f:
        G = pickle.load(f)
        
    if not isinstance(G, nx.MultiDiGraph):
        raise TypeError(f"Loaded object from {path} is not a NetworkX MultiDiGraph")
        
    return G

if __name__ == "__main__":
    import argparse
    from ai_service.layer4.segment_lookup import SegmentLookup
    
    parser = argparse.ArgumentParser(description="Graph Persistence Utility")
    parser.add_argument("--load", type=str, help="Path to load the graph from")
    args = parser.parse_args()
    
    if args.load:
        print(f"Loading graph from {args.load}...")
        G = load_graph(args.load)
        print(f"Graph loaded successfully.")
        print(f"Nodes: {len(G.nodes)}")
        print(f"Edges: {len(G.edges)}")
        
        print("Rebuilding deterministic segment index...")
        lookup = SegmentLookup(G)
        print(f"Index built successfully with {len(lookup.index)} mapped segments.")
