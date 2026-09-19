import networkx as nx
import pickle

class DuplicateSegmentIDError(Exception):
    pass

class SegmentNotFoundError(Exception):
    pass

class SegmentLookup:
    """
    Provides deterministic and efficient O(1) lookups for graph edges using their segment_id.
    Ensures that segment IDs are unique and mapped correctly to their NetworkX MultiDiGraph (u, v, k) keys.
    """
    def __init__(self, G: nx.MultiDiGraph):
        if not isinstance(G, nx.MultiDiGraph):
            raise TypeError("Expected a networkx MultiDiGraph")
            
        self.G = G
        self.index = {}
        self._build_index()

    def _build_index(self):
        for u, v, k, data in self.G.edges(keys=True, data=True):
            seg_id = data.get("segment_id")
            if not seg_id:
                continue
            
            # Normalize ID for robust lookups
            norm_id = str(seg_id).strip().upper()
            
            if norm_id in self.index:
                raise DuplicateSegmentIDError(f"Duplicate segment ID detected during index construction: {norm_id}")
                
            self.index[norm_id] = (u, v, k)
            
    def get_segment(self, segment_id: str) -> dict:
        """
        Retrieves the edge information associated with a given segment ID.
        Fails clearly if the segment is not found.
        """
        if not segment_id:
            raise ValueError("Segment ID cannot be empty.")
            
        norm_id = str(segment_id).strip().upper()
        
        if norm_id not in self.index:
            raise SegmentNotFoundError(f"Segment ID not found in graph: {norm_id}")
            
        u, v, k = self.index[norm_id]
        
        data = self.G.edges[u, v, k]
        
        response = {
            "source_node": u,
            "destination_node": v,
            "edge_key": k,
        }
        # Merge edge data into response
        response.update(data)
        
        return response

if __name__ == "__main__":
    import os
    
    base_dir = os.path.dirname(__file__)
    graph_path = os.path.join(base_dir, "data", "routing_graph.pkl")
    
    if os.path.exists(graph_path):
        print(f"Loading graph from {graph_path}...")
        with open(graph_path, "rb") as f:
            G = pickle.load(f)
            
        print("Building segment index...")
        lookup = SegmentLookup(G)
        print(f"Index built successfully. Indexed {len(lookup.index)} segments.")
        
        # Example lookups
        sample_keys = list(lookup.index.keys())[:3]
        if sample_keys:
            print("\nExample lookups:")
            for k in sample_keys:
                print(f"Lookup for {k}:")
                result = lookup.get_segment(k)
                print(f" -> Source: {result['source_node']}, Dest: {result['destination_node']}, Length: {result.get('length_m')}m")
    else:
        print("Graph file not found. Run graph_builder.py first.")
