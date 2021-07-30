import rpyc

if __name__ == "__main__":
   c = rpyc.connect("localhost", 18861)
   c.root.doserOperation('OPERATE/Drain Pump')