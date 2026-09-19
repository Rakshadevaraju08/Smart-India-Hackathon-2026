import unittest
import numpy as np
import scipy.sparse as sp
import time

from ai_service.layer3.graph_builder import StreetDrainageGraph
from ai_service.layer3.mass_conservation_loss import MassConservationConstraint, PhysicsInformedSaintVenantLoss
from ai_service.layer3.surrogate_model import PhysicsInformedGraphSurrogate, HORIZONS_MIN

class TestLayer3PrecisionArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = StreetDrainageGraph()
        cls.surrogate = PhysicsInformedGraphSurrogate()
        cls.constraint = MassConservationConstraint(tolerance_pct=0.0001)
        cls.pinn_loss = PhysicsInformedSaintVenantLoss()

    def test_01_graph_directed_hydraulic_operator(self):
        A_hat = self.graph.get_directed_adjacency_operator()
        self.assertIsNotNone(A_hat)
        self.assertEqual(A_hat.shape, (7894, 7894))
        self.assertGreater(A_hat.nnz, 50000)
        row_sums = np.array(A_hat.sum(axis=1)).flatten()
        np.testing.assert_allclose(row_sums, 1.0, rtol=1e-5, atol=1e-5)
        x = np.random.uniform(10.0, 50.0, 7894).astype(np.float32)
        y = A_hat.T.dot(x)
        diff = abs(float(np.sum(y)) - float(np.sum(x)))
        rel_err = diff / float(np.sum(x))
        self.assertLess(rel_err, 1e-6)

    def test_02_analytical_mass_conservation_discrepancy_bound(self):
        n_nodes = self.surrogate.n_nodes
        for storm_rate in [25.0, 65.0, 110.0]:
            for clog in [0.0, 0.35, 0.70]:
                rain_vectors = {h: np.full(n_nodes, storm_rate, dtype=np.float32) for h in HORIZONS_MIN}
                res = self.surrogate.predict_multi_horizon(rain_vectors, clogging_modifier=clog)
                for h in HORIZONS_MIN:
                    metric = res['metrics'][f'T+{h}m']
                    self.assertTrue(metric['mass_conserved'])
                    self.assertLessEqual(metric['mass_error_pct'], 0.0001)

    def test_03_physics_informed_saint_venant_loss_formulation(self):
        n_nodes = self.surrogate.n_nodes
        areas = np.full(n_nodes, 3500.0, dtype=np.float64)
        elev = self.graph.get_node_feature_matrix()['elevations'].astype(np.float64)
        edge_tensors = self.graph.get_edge_tensors()
        A_hat = self.graph.get_directed_adjacency_operator()
        h_pred = np.random.uniform(0.05, 0.40, n_nodes).astype(np.float64)
        h_curr = np.zeros(n_nodes, dtype=np.float64)
        q_inflow = np.full(n_nodes, 0.05, dtype=np.float64)
        loss_dict = self.pinn_loss.compute_total_loss(
            h_pred_m=h_pred,
            h_curr_m=h_curr,
            elevations_m=elev,
            dt_seconds=3600.0,
            A_hat_csr=A_hat,
            q_net_inflow_m3_s=q_inflow,
            areas_m2=areas,
            edge_src=edge_tensors['edge_src'],
            edge_dst=edge_tensors['edge_dst'],
            edge_lengths_m=edge_tensors['edge_lengths_m']
        )
        self.assertIn('loss_total', loss_dict)
        self.assertIn('loss_continuity', loss_dict)
        self.assertIn('loss_momentum', loss_dict)
        self.assertGreater(loss_dict['loss_total'], 0.0)

    def test_04_cpu_inference_latency_budget_under_30ms(self):
        n_nodes = self.surrogate.n_nodes
        rain_vectors = {h: np.full(n_nodes, 55.0, dtype=np.float32) for h in HORIZONS_MIN}
        _ = self.surrogate.predict_multi_horizon(rain_vectors)
        times = []
        for _ in range(15):
            t0 = time.perf_counter()
            _ = self.surrogate.predict_multi_horizon(rain_vectors)
            times.append((time.perf_counter() - t0) * 1000.0)
        mean_latency = float(np.mean(times))
        p95_latency = float(np.percentile(times, 95))
        min_latency = float(np.min(times))
        print(f'\n[CPU Benchmark] Mean: {mean_latency:.2f}ms, P95: {p95_latency:.2f}ms, Min: {min_latency:.2f}ms')
        self.assertLess(mean_latency, 30.0)
        self.assertLess(p95_latency, 30.0)

if __name__ == '__main__':
    unittest.main()