from storage.intraday_repository import IntradayRepository


SYMBOL = "Bra50Oct26"


def main():
    repository = IntradayRepository()

    repository.prepare_symbol(
        SYMBOL
    )

    print()
    print("Base intraday preparada.")
    print(f"Símbolo: {SYMBOL}")
    print("Ticks: data/intraday/ticks.db")
    print("Renko: data/intraday/renko.db")


if __name__ == "__main__":
    main()