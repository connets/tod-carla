//
// Copyright (C) 2011 OpenSim Ltd.
//
// SPDX-License-Identifier: LGPL-3.0-or-later
//


#ifndef _TODAGENTAPP_H
#define _TODAGENTAPP_H
#include <omnetpp.h>
#include "inet/applications/base/ApplicationBase.h"
#include "inet/transportlayer/contract/udp/UdpSocket.h"
#include "carla_omnet/CarlaCommunicationManager.h"

using namespace omnetpp;
using namespace inet;

/**
 * UDP application. See NED for more info.
 */
class TODAgentApp : public ApplicationBase, public UdpSocket::ICallback
{
protected:
    UdpSocket socket;
    int numEchoed; // just for WATCH

    virtual int numInitStages() const override { return NUM_INIT_STAGES; }
    virtual void initialize(int stage) override;
    virtual void handleMessageWhenUp(cMessage *msg) override;
    virtual void finish() override;
    virtual void refreshDisplay() const override;
    void processPacket(Packet *pk);

    virtual void handleStartOperation(LifecycleOperation *operation) override;
    virtual void handleStopOperation(LifecycleOperation *operation) override;
    virtual void handleCrashOperation(LifecycleOperation *operation) override;

    virtual void socketDataArrived(UdpSocket *socket, Packet *packet) override;
    virtual void socketErrorArrived(UdpSocket *socket, Indication *indication) override;
    virtual void socketClosed(UdpSocket *socket) override;
private:
    CarlaCommunicationManager* carlaCommunicationManager;
};


#endif

