CC ?= gcc
INC_PATH ?= $(realpath ../inc)
LIB_PATH ?= $(realpath ../lib)
LIBS ?= $(wildcard $(LIB_PATH)/*.a) -pthread -lrt -lm
LDFLAGS :=-g -L$(LIB_PATH)
CFLAGS +=-g -I$(INC_PATH)

EXAMPLES=CollisionWarning

.PHONY: all

all: $(EXAMPLES)

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<

CollisionWarning: src/CollisionWarning.o src/lib/frozen.o src/lib/send.o src/lib/receive.o src/lib/auxFunctions.o src/lib/collisionPrevisionAlg.o src/lib/itsmsg_funcs.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(LIBS) -Wl,-rpath,'$$ORIGIN/../../lib'

clean:
	rm -f *~ *.o $(EXAMPLES)
	rm -f *~ *.o src/$(EXAMPLES).o
	rm -f *~ *.o src/lib/auxFunctions.o
	rm -f *~ *.o src/lib/frozen.o
	rm -f *~ *.o src/lib/send.o
	rm -f *~ *.o src/lib/receive.o
	rm -f *~ *.o src/lib/collisionPrevisionAlg.o
	rm -f *~ *.o src/lib/itsmsg_funcs.o
