import pandas as pd
df = pd.read_csv('/home/stefano/Documents/tesi/tod-simulator/cooperative-perception/results/unprotected_left_turn-1-20241117-10:39:06-126201/omnet.csv')

# Filter rows based on column: 'module'
df = df[df['module'].str.contains("oneTOD.server.app", regex=False, na=False, case=False)]

# Filter rows based on column: 'name'
df = df[
    (df['name'].str.contains("packetReceived:count", regex=False, na=False, case=False)) | 
    (df['name'].str.contains("packetReceived:sum(packetBytes)", regex=False, na=False, case=False)) |
    (df['name'].str.contains("packetReceived:vector(packetBytes)", regex=False, na=False, case=False)) |
    (df['name'].str.contains("packetReceivedDelay:vector", regex=False, na=False, case=False)) |
    (df['name'].str.contains("throughput:vector", regex=False, na=False, case=False)) |
    (df['name'].str.contains("typename", regex=False, na=False, case=False))
]


print(df)