#ifndef __CARLACOMMUNICATIONMANAGER_H_
#define __CARLACOMMUNICATIONMANAGER_H_

#include <string>
#include <list>
#include "omnetpp.h"
#include <zmq.hpp>
#include <iostream>
#include <chrono>
#include <thread>

#include <map>
#include <memory>
#include <list>
#include <queue>
#include <fstream>
#include <nlohmann/json.hpp>

using namespace omnetpp;
using namespace std;

using json = nlohmann::json;

namespace sta {

    struct simulation_step_answer {
            std::string location;
    };
    inline void to_json(json& j, const simulation_step_answer& s) {
        j = json{{"location", s.location}};
    }

    inline void from_json(const json& j, simulation_step_answer& s) {
        j.at("location").get_to(s.location);
    }
} 

namespace ha {

struct handshake_answer {
        float timestamp;
};
inline void to_json(json& j, const handshake_answer& s) {
    j = json{{"timestamp", s.timestamp}};
}

inline void from_json(const json& j, handshake_answer& s) {
    j.at("timestamp").get_to(s.timestamp);
}
}
namespace rma {

    struct receive_message_answer {
            int msg_id;
            int size;
    };
    inline void to_json(json& j, const receive_message_answer& s) {
        j = json{{"msg_id", s.msg_id}};
        j = json{{"size", s.size}};
    }

    inline void from_json(const json& j, receive_message_answer& s) {
        j.at("msg_id").get_to(s.msg_id);
        j.at("size").get_to(s.size);
    }
} 
class CarlaCommunicationManager: public cSimpleModule {//, public cISimulationLifecycleListener {
public:
    CarlaCommunicationManager();
    ~CarlaCommunicationManager();


    double coSimulationStartTimestamp;
    rma::receive_message_answer receiveMessage(int msg_id);

    void connect();
    bool isConnected() const
    {
        return true; //static_cast<bool>(connection);
    }
protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;

private:
    sta::simulation_step_answer doSimulationTimeStep();
    bool connection;
    string protocol;
    string host;
    double simulationTimeStep;
    int port;
    zmq::context_t context;
    zmq::socket_t socket;
};

#endif
