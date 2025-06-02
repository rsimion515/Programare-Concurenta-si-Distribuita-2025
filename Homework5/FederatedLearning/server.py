import flwr as fl

def main():
    config = fl.server.ServerConfig(num_rounds=5)

    strategy = fl.server.strategy.FedAvg(
        fraction_fit=1.0,
        min_fit_clients=3,
        min_available_clients=3,
    )
    fl.server.start_server(server_address="0.0.0.0:8080", strategy=strategy, config=config)

if __name__ == "__main__":
    main()
