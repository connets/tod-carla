#include "CarlaCommunicationManager.h"
#include "inet/applications/base/ApplicationPacket_m.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/TagBase_m.h"
#include "inet/common/TimeTag_m.h"
#include "inet/common/lifecycle/ModuleOperations.h"
#include "inet/common/packet/Packet.h"
#include "inet/networklayer/common/FragmentationTag_m.h"
#include "inet/networklayer/common/L3AddressResolver.h"
#include "inet/transportlayer/contract/udp/UdpControlInfo_m.h"
using namespace inet;
using namespace std;

Define_Module(CarlaCommunicationManager);

CarlaCommunicationManager::CarlaCommunicationManager(){

}
CarlaCommunicationManager::~CarlaCommunicationManager(){

}

void CarlaCommunicationManager::initialize()
{
    cSimpleModule::initialize();
    protocol = par("protocol").stringValue();
    host = par("host").stringValue();
    port = par("port");
    simulationTimeStep = par("simulationTimeStep");
    this->context = zmq::context_t {1};
    this->socket = zmq::socket_t{context, zmq::socket_type::req};
    int timeout_ms = 100000;
    this->socket.setsockopt(ZMQ_RCVTIMEO, timeout_ms); // set timeout to value of timeout_ms
    this->socket.setsockopt(ZMQ_SNDTIMEO, timeout_ms); // set timeout to value of timeout_ms
    EV_INFO << "CarlaCommunicationManagerLog " << "Finish initialize" << endl;
    connect();

}

sta::simulation_step_answer CarlaCommunicationManager::doSimulationTimeStep(){
    float ts = simTime().dbl();
    EV_INFO << "CarlaCommunicationManager: " << ts;
    const std::string data{"{\"request_type\":\"simulation_step\", \"timestamp\":" + std::to_string(ts) + "}"};
    int len = sizeof(data);
    this->socket.send(zmq::buffer(data), zmq::send_flags::none);
    zmq::message_t reply{};
    if (!socket.recv(reply, zmq::recv_flags::none)){
        std::cout << "ERRORE";
    }
    json j = json::parse(reply.to_string());
    auto a = j.get<sta::simulation_step_answer>();

    return a;
}


rma::receive_message_answer CarlaCommunicationManager::receiveMessage(int msg_id){
    float ts = simTime().dbl();
    const std::string data{"{\"request_type\":\"receive_msg\", \"timestamp\":" + std::to_string(ts) + ", \"msg_id\":" + std::to_string(msg_id) + "}"};
    int len = sizeof(data);
    this->socket.send(zmq::buffer(data), zmq::send_flags::none);
    zmq::message_t reply{};
    if (!socket.recv(reply, zmq::recv_flags::none)){
        std::cout << "ERRORE";
    }
    json j = json::parse(reply.to_string());
    rma::receive_message_answer a = j.get<rma::receive_message_answer>();
    return a;
}

void CarlaCommunicationManager::connect(){
    float ts = simTime().dbl();

    string addr = protocol + "://" + host + ":" + std::to_string(port);
    EV << "Trying connecting to: " << addr << endl;
    socket.connect("tcp://localhost:5555");
    const std::string data{"{\"request_type\":\"handshake\", \"timestamp\":" + std::to_string(ts) + "}"};

    socket.send(zmq::buffer(data), zmq::send_flags::none);
    zmq::message_t reply{};
    this->socket.recv(reply, zmq::recv_flags::none);
    json j = json::parse(reply.to_string());
    ha::handshake_answer a = j.get<ha::handshake_answer>();
    coSimulationStartTimestamp = a.timestamp;
    EV_INFO << "CarlaCommunicationManagerLog " << "connection message: " << reply.to_string() << endl;
    EV_INFO << "CarlaCommunicationManagerLog " << "co-simulation starts at: " << std::to_string(a.timestamp) << endl;
    cMessage *simulationTimeStepEvent = new cMessage("simulationTimeStep");

    scheduleAt(coSimulationStartTimestamp + simulationTimeStep, simulationTimeStepEvent);
}

void CarlaCommunicationManager::handleMessage(cMessage *msg)
{
    // msg->getName() is name of the msg object, here it will be "tictocMsg".
    this->doSimulationTimeStep();
    EV_INFO << "HERE : =>  " << this->simulationTimeStep << endl;
    scheduleAt(simTime() + this->simulationTimeStep, msg);
}

