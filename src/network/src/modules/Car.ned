package src.modules;
import simu5g.nodes.NR.NRUe;
import org.car2x.veins.modules.nic.Nic80211p;
import inet.linklayer.contract.IWirelessInterface;

module Car extends NRUe
{
    parameters:

        @display("i=device/car,,0;is=vs;bgb=,,,,0");

        //# Mobility
        mobility.typename = default("VeinsInetMobility");

        //# Network Layer specs
        *.routingTableModule = default(absPath(".ipv4.routingTable"));

        numApps = default(2);
        app[0].typename = "DeviceApp";
        app[0].localPort = 4500;
		app[0].UALCMPAddress = "ualcmp";
		app[0].UALCMPPort = 1000;
		app[0].appPackageSource = "ApplicationDescriptor/VehicleControlApp.json";
		
        app[1].typename = "VehicleControlApp";
        app[1].startTime = 1s;
		app[1].stopTime = 30s;
		app[1].deviceAppAddress = "car[" + string(index) + "]";
		app[1].deviceAppPort = 4500;
//        
//    submodules:
//        controller: LowLevelController {
//            @display("p=126.84,521.856;i=block/cogwheel");
//        }
        
}

