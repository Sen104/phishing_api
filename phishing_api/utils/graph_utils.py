import networkx as nx
import torch
from torch_geometric.data import Data

def email_to_pyg_graph(email_text, label, vectorizer, window_size=2):
    tokens = email_text.split()
    G = nx.Graph()

    for token in tokens:
        G.add_node(token)

    for i in range(len(tokens)):
        for j in range(i + 1, min(i + 1 + window_size, len(tokens))):
            G.add_edge(tokens[i], tokens[j])

    tfidf_vector = vectorizer.transform([email_text])
    tfidf_vocab = vectorizer.get_feature_names_out()

    for node in G.nodes:
        node_vector = [0.0] * len(tfidf_vocab)
        if node in tfidf_vocab:
            idx = list(tfidf_vocab).index(node)
            node_vector[idx] = tfidf_vector[0, idx]
        G.nodes[node]['x'] = node_vector

    node_to_index = {node: i for i, node in enumerate(G.nodes)}
    edge_index = [[node_to_index[src], node_to_index[dst]] for src, dst in G.edges()]
    edge_index += [[j, i] for i, j in edge_index]  # Undirected

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    x = [G.nodes[node]['x'] for node in G.nodes]
    x = torch.tensor(x, dtype=torch.float)
    y = torch.tensor([label], dtype=torch.long)

    return Data(x=x, edge_index=edge_index, y=y)
