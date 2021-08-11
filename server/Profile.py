class Profile:

    prefix = "uu"
    identifier = "unregistered"

    def __init__(self, firstname="unregistered", lastname="user"):
        self.fname = firstname.lower()
        self.lname = lastname.lower()
        self.prefix = self.fname[0].lower()+self.lname[0].lower()
        self.identifier = self.fname+"_"+self.lname

    def toStringProfile(self):
        return self.firstname+" "+self.lastname+" using prefix: "+self.prefix
