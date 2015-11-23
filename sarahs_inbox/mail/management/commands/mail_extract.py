from django.core.management.base import NoArgsCommand, BaseCommand
import re, os, hashlib

class Command(BaseCommand):
    help = "Extract Kagan email data into individual files."    

    def emit(self, filename, count, buf):        
        filename = filename.replace('.txt', '')
        out = open('parsed/extracted/%s-%d.txt' % (filename, count), 'w')
        out.write("".join(buf))
        out.close()
        

    def handle(self, *args, **options):

        re_record_start = re.compile(r'^\s*Unknown\s*$')
        re_garbage = re.compile(r'(^\s*Page\s+\d+|^\s*Unknown\s*$)')

        files = []
        count = 0
        for p in args:
            if os.path.exists(p):
                for filename in os.listdir(p):
                    email_index = 0

                    buf = []
                    collecting = False
                    f = open('%s/%s' % (p, filename), 'r')
                    while True:
                        line = f.readline()
                        if not line:
                            break                


                        # new record? clear out the buffer (if there is a buffer)
                        if re_record_start.match(line) is not None:
                            if collecting and len(buf)>0:
                                self.emit(filename, email_index, buf)
                                count += 1
                                email_index += 1
                            collecting = True
                            buf = []


                        # add to buffer... if not garbage
                        if re_garbage.search(line) is None:
                            buf.append(line)

                    f.close()            
            
        
        print "Extracted %d mail objects" % count

            
                
