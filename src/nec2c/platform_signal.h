/* SPDX-License-Identifier: BSD-2-Clause */
/*
 * Project-authored maintained portability code.
 * Original NEC2C source provenance remains documented by this repository.
 */

#ifndef PLATFORM_SIGNAL_H
#define PLATFORM_SIGNAL_H 1

#include <signal.h>

/*
 * Preserve POSIX sigaction behavior for MSYS and Cygwin. Native MinGW/UCRT64
 * uses the ISO C signal interface for the same five signals and handler.
 */
static int nec2c_register_signal_handlers( void (*handler)(int) )
{
#if defined(_WIN32) && !defined(__CYGWIN__) && !defined(__MSYS__)
  if( signal( SIGINT, handler ) == SIG_ERR )
    return( -1 );
  if( signal( SIGSEGV, handler ) == SIG_ERR )
    return( -1 );
  if( signal( SIGFPE, handler ) == SIG_ERR )
    return( -1 );
  if( signal( SIGTERM, handler ) == SIG_ERR )
    return( -1 );
  if( signal( SIGABRT, handler ) == SIG_ERR )
    return( -1 );
#else
  struct sigaction sa_new, sa_old;

  sa_new.sa_handler = handler;
  sigemptyset( &sa_new.sa_mask );
  sa_new.sa_flags = 0;

  sigaction( SIGINT,  &sa_new, &sa_old );
  sigaction( SIGSEGV, &sa_new, 0 );
  sigaction( SIGFPE,  &sa_new, 0 );
  sigaction( SIGTERM, &sa_new, 0 );
  sigaction( SIGABRT, &sa_new, 0 );
#endif

  return( 0 );
}

#endif /* PLATFORM_SIGNAL_H */
