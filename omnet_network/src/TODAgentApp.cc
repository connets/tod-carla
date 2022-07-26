//
// Copyright (C) 2011 OpenSim Ltd.
//
// SPDX-License-Identifier: LGPL-3.0-or-later
//


#include "TODAgentApp.h"

#include "inet/common/ModuleAccess.h"
#include "inet/common/Simsignals.h"
#include "inet/networklayer/common/L3AddressTag_m.h"
#include "inet/transportlayer/common/L4PortTag_m.h"
#include "inet/transportlayer/contract/udp/UdpControlInfo_m.h"
using namespace inet;
using namespace std;
#include "packets/TODMessage_m.h"
#include "carla_omnet/CarlaCommunicationManager.h"


Define_Module(TODAgentApp);

void TODAgentApp::initialize(int stage)
{
    ApplicationBase::initialize(stage);

    if (stage == INITSTAGE_LOCAL) {
        // init statistics
        numEchoed = 0;
        WATCH(numEchoed);
        carlaCommunicationManager = check_and_cast<CarlaCommunicationManager*>(
                getParentModule()->getParentModule()->getSubmodule("carlaCommunicationManager"));
    }
}

void TODAgentApp::handleMessageWhenUp(cMessage *msg)
{
    socket.processMessage(msg);
}

void TODAgentApp::socketDataArrived(UdpSocket *socket, Packet *pk)
{
    // determine its source address/port
    EV << "TODAgentApp  " << "received msg" << endl;
    const auto& received_payload = pk->peekData<TODMessage>();

    rma::receive_message_answer answer = carlaCommunicationManager->receiveMessage(received_payload->getMsgId());

    L3Address remoteAddress = pk->getTag<L3AddressInd>()->getSrcAddress();
    int srcPort = pk->getTag<L4PortInd>()->getSrcPort();

    EV_INFO << "TODAgentApp " << "message arrived with id " << received_payload->getMsgId() << endl;
    EV_INFO << "TODAgentApp " << simTime().dbl() * 1000;
    Packet *packet = new Packet("Response TOD");

    const auto& payload = makeShared<TODMessage>();
    payload->setChunkLength(B(123));
    payload->setMsgId(answer.msg_id);
    //payload->addTag<CreationTimeTag>()->setCreationTime(123);
    packet->insertAtBack(payload);
    // statistics
    delete pk;

    numEchoed++;
    emit(packetSentSignal, packet);
    // send back
    socket->sendTo(packet, remoteAddress, srcPort);
}


void TODAgentApp::processPacket(Packet *pk)
{
    if (pk->getKind() == UDP_I_ERROR) {
        EV_WARN << "UDP error received\n";
        delete pk;
        return;
    }

    if (pk->hasPar("msgId")) {
        int msgId = pk->par("msgId");
    }

    EV_INFO << "Received packet: " << UdpSocket::getReceivedPacketInfo(pk) << endl;
    emit(packetReceivedSignal, pk);
    delete pk;
}

void TODAgentApp::socketErrorArrived(UdpSocket *socket, Indication *indication)
{
    EV_WARN << "Ignoring UDP error report " << indication->getName() << endl;
    delete indication;
}

void TODAgentApp::socketClosed(UdpSocket *socket)
{
    if (operationalState == State::STOPPING_OPERATION)
        startActiveOperationExtraTimeOrFinish(par("stopOperationExtraTime"));
}

void TODAgentApp::refreshDisplay() const
{
    ApplicationBase::refreshDisplay();

    char buf[40];
    sprintf(buf, "echoed: %d pks", numEchoed);
    getDisplayString().setTagArg("t", 0, buf);
}

void TODAgentApp::finish()
{
    ApplicationBase::finish();
}

void TODAgentApp::handleStartOperation(LifecycleOperation *operation)
{
    socket.setOutputGate(gate("socketOut"));
    int localPort = par("localPort");
    socket.bind(localPort);
    MulticastGroupList mgl = getModuleFromPar<IInterfaceTable>(par("interfaceTableModule"), this)->collectMulticastGroups();
    socket.joinLocalMulticastGroups(mgl);
    socket.setCallback(this);
}

void TODAgentApp::handleStopOperation(LifecycleOperation *operation)
{
    socket.close();
    delayActiveOperationFinish(par("stopOperationTimeout"));
}

void TODAgentApp::handleCrashOperation(LifecycleOperation *operation)
{
    if (operation->getRootModule() != getContainingNode(this)) // closes socket when the application crashed only
        socket.destroy(); // TODO  in real operating systems, program crash detected by OS and OS closes sockets of crashed programs.
    socket.setCallback(nullptr);
}


