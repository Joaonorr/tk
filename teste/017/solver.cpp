#include <iostream>
#include <vector>
#include <utility>
#include <aux.hpp>

enum Coin {M10, M25, M50, M100};
struct CoinDef {
    float value;
    int volume;
};

CoinDef getDef(Coin coin) {
    switch (coin) {
        case M10: return {0.1, 1};
        case M25: return {0.25, 2};
        case M50: return {0.50, 3};
        case M100: return {1, 4};
    }
    return {0, 0};
}


class Item {
    std::string label;
    int volume;
public:
    Item(std::string label, int volume) : label(label), volume(volume) { //todo}
    int getVolume() const {
        return {}; // todo return volume; }
    std::string getLabel() const {
        return {}; // todo return label; }
    void setVolume(int volume) { //todo this->volume = volume; }
    void setLabel(std::string label) { //todo this->label = label; }
    std::string str() const {
        return {}; // todo
    }
};

std::ostream& operator<<(std::ostream& os, const Item& item) {
    return os << item.str();
}

class Pig {
    std::vector<std::string> itens;
    double value {0};
    int volume {0};
    int volumeMax {0};
    bool broken {false};

public:
    Pig(int volumeMax = 0) :
     volumeMax(volumeMax) {
        return {}; // todo
    }
    
    bool addCoin(Coin coin) {
        return {}; // todo
    }

    bool addItem(Item item) {
        return {}; // todo



    }

    bool breakPig() {
        return {}; // todo
    }

    double getCoins() {
        return {}; // todo
    }

    std::string getItens() {
        return {}; // todo
    }

    std::string str() const {
        std::stringstream ss;
        ss << aux::fmt(this->itens) << " : "
           << aux::fmt(value) << "$ : "
           << volume <<  "/" << volumeMax << " : " 
           <<  (broken ? "broken" : "unbroken");
        return ss.str();
    }
};

std::ostream& operator<<(std::ostream& os, const Pig& pig) {
    return os << pig.str();
}

int main() {
    aux::Chain chain;
    aux::Param par;

    Pig pig;
    
    auto toInt = aux::to<int>;

    chain["init"] = [&]() { pig = Pig(toInt(par[1])); };
    chain["addCoin"] = [&]() { 
        if      (par[1] == "10") pig.addCoin(M10);
        else if (par[1] == "25") pig.addCoin(M25);
        else if (par[1] == "50") pig.addCoin(M50);
        else if (par[1] == "100") pig.addCoin(M100);
    };
    chain["addItem"] = [&]() { pig.addItem(Item(par[1], toInt(par[2]))); };
    chain["break"] = [&]() { pig.breakPig(); };
    chain["getCoins"] = [&]() { aux::show << pig.getCoins(); };
    chain["getItens"] = [&]() { aux::show << pig.getItens(); };
    chain["show"] = [&]() {     aux::show << pig.str(); };

    aux::execute(chain, par);
}