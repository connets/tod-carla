package tod_network.carla_omnet;

simple CarlaCommunicationManager
{
    
    
    parameters:
        @class(CarlaCommunicationManager);
        
        double connectAt @unit("s") = default(0s);  // when to connect to TraCI server (must be the initial timestep of the server)
        double firstStepAt @unit("s") = default(-1s);  // when to start synchronizing with the TraCI server (-1: immediately after connecting)
        double updateInterval @unit("s") = default(1s);  // time interval of hosts' position updates
        double updateTimeStep @unit("s") = default(5ms);  // time interval of hosts' position updates

	
        string host = default("localhost");  // server hostname
        string protocol = default("tcp");  // server hostname
        double simulationTimeStep @unit("s") = default(5ms);
        int port = default(5555);  // server port (-1: automatic)
        int seed = default(-1); // seed value to set in launch configuration, if missing (-1: current run number)
        bool autoShutdown = default(true);  // Shutdown module as soon as no more vehicles are in the simulation
        
}

