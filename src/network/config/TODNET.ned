package config;
import inet.node.bgp.BgpRouter;
import inet.node.ethernet.Eth10G;
import inet.node.ethernet.Eth10M;

import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import simu5g.common.binder.Binder;
import simu5g.world.radio.LteChannelControl;
import simu5g.common.carrierAggregation.CarrierAggregation;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.networklayer.ipv4.RoutingTableRecorder;
import simu5g.nodes.NR.gNodeB;
import simu5g.nodes.mec.MECHost;
import simu5g.nodes.Upf;
import simu5g.nodes.mec.UALCMP.UALCMP;
import simu5g.nodes.mec.MECOrchestrator.MecOrchestrator;
//import simu5g.nodes.NR.NRUe;
//import simu5g.nodes.cars.NRCar;

import org.car2x.veins.subprojects.veins_inet.VeinsInetManager;
//import simulator_5g_v2x.modules.globalplatoonsmanager.GlobalPlatoonsManager;
//import simulator_5g_v2x.modules.Car;

network TODNET
{
    parameters:
        double playgroundSizeX @unit(m); // x size of the area the nodes are in (in meters)
        double playgroundSizeY @unit(m); // y size of the area the nodes are in (in meters)
        double playgroundSizeZ @unit(m); // z size of the area the nodes are in (in meters)

        double bbdelay @unit(s) = default(1ms);

    submodules:
        binder: Binder {
            @display("p=45,283;is=s");
        }
        channelControl: LteChannelControl {
            @display("p=120,283;is=s");
        }
        carrierAggregation: CarrierAggregation {
            @display("p=99,344;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=218,350;is=s");
        }
        routingRecorder: RoutingTableRecorder {
            @display("p=292,283;is=s");
        }
        gB0: gNodeB {
            @display("p=200, 100");
        }
      
        upf: Upf {
            @display("p=323,77");
        }
        //MEC
        mecHost: MECHost {
            @display("p=411,216");
        }
        ualcmp: UALCMP {
            @display("p=239,216");
        }
        mecOrchestrator: MecOrchestrator {
            @display("p=142,216");
        }

		//Aggiunta ------
//        veinsManager: VeinsInetManager {
//            @display("p=1440,283;is=s");
//        }
//        globalPlatoonsManager: GlobalPlatoonsManager;
//        car[0]: Car;
    connections:

        upf.filterGate <--> Eth10G <--> ualcmp.ppp++;
        ualcmp.toMecOrchestrator --> mecOrchestrator.fromUALCMP;
        ualcmp.fromMecOrchestrator <-- mecOrchestrator.toUALCMP;

        //upf.pppg++ <--> Eth10G <--> router.pppg++;
        //router.pppg++ <--> {delay = 1ms; datarate = 10Mbps;} <--> router1.pppg++;
        //router.pppg++ <--> Eth10M <--> router1.pppg++;
        //router.pppg++ <--> Eth10G {length = replaceUnit(bbdelay * 2e8, "m");} <--> router1.pppg++;
        //router1.pppg++ <--> Eth10G <--> mecHost.pppENB++;

        upf.pppg++ <--> Eth10G <--> mecHost.pppENB++;

        upf.pppg++ <--> Eth10G <--> gB0.ppp;



}