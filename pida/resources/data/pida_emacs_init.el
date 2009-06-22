;; Emacs client script for PIDA
;;
;; Copyright (C) 2008 Stephan Peijnik
;;
;; Based on "Emacs client script for Pida." 
;; by David Soulayrol <david.soulayrol@anciens.enib.fr>
;;
;; Permission is hereby granted, free of charge, to any person obtaining a copy
;; of this software and associated documentation files (the "Software"), to 
;; deal in the Software without restriction, including without limitation the 
;; rights to use, copy, modify, merge, publish, distribute, sublicense, 
;; and/or sell copies of the Software, and to permit persons to whom the 
;; Software is furnished to do so, subject to the following conditions:
;;
;; The above copyright notice and this permission notice shall be included in
;; all copies or substantial portions of the Software.
;;
;; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
;; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
;; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
;; AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
;; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
;; FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
;; DEALINGS IN THE SOFTWARE.

(defconst pida-dbus-ns (concat "uk.co.pida.pida." (getenv "PIDA_DBUS_UUID")))

(defun mycomplete (&optional prefix)
  (interactive)
  (setq bufstr (buffer-string))
  (setq bufpos (- (point) 1))
  (setq compl (dbus-call-method :session pida-dbus-ns
 		    "/uk/co/pida/pida/language"
		    "uk.co.pida.pida.language" 
		    "get_completions"
		    prefix bufstr bufpos))
)

(defun mycomplete-wrapper (prefix maxnum)
  "Wrapper around `dabbrev--find-all-completions',
     to use as a `completion-function'."
  (let ((completions (mycomplete prefix)))
    (when maxnum
      (setq completions
	    (butlast completions (- (length completions) maxnum))))
    completions))

(defun prepare() 
  (interactive)
  (setq lp (concat 
 	    (file-name-directory (expand-file-name "pida_emacs_init.el"))
 	    "pida/resources/data/emacs/"))
  (setq load-path (append (list lp)  load-path))
  (require 'dbus)
  (require 'auto-overlay-common)
  (setq completion-function 'mycomplete-wrapper)
  (require 'completion-ui)
  )

(prepare)



;;(dbus-ping :session pida-dbus-ns)


(defconst pida-connection-terminator "\n"
  "The terminator used to send notifications to PIDA")

(defvar pida-connection nil
  "The socket to communicate with PIDA")

;; pida-register-hooks
;;
;; Registers all hooks.
(defun pida-register-hooks ()
  (add-hook 'find-file-hooks
	    'pida-find-file)
  (add-hook 'after-save-hook
	    'pida-after-save)
  (add-hook 'kill-buffer-hook
	    'pida-kill-buffer)
  (add-hook 'window-configuration-change-hook
	    'pida-window-configuration-change)
  (add-hook 'kill-emacs-hook
	    'pida-kill-emacs))

;; pida-unregister-hooks
;;
;; Unregisters all hooks.
(defun pida-unregister-hooks ()
  (remove-hook 'find-file-hooks
	       'pida-find-file)
  (remove-hook 'after-save-hook
	       'pida-after-save)
  (remove-hook 'kill-buffer-hook
	       'pida-kill-buffer)
  (remove-hook 'window-configuration-change-hook
	       'pida-window-configuration-change)
  (remove-hook 'kill-emacs-hook
	       'pida-kill-emacs))

;; pida-quit
;;
;; Quits emacs.
(defun pida-quit ()
  (pida-disconnect)
  (kill-emacs))

;;
;; pida-check-connection
;;
;; Checks the network connection. A return value of non-nil means
;; the connection is alive, everything else means it is dead.
(defun pida-check-connection ()
  (if (equal nil pida-connection)
      nil
      (not (equal 'closed (process-status pida-connection)))))

;; pida-send-message (message)
;;
;; Sends a message to PIDA.                                                    
(defun pida-send-message (message)
  (if (pida-check-connection)
      (process-send-string "pida-connection"
                           (concat message pida-connection-terminator))))

;; pida-connect (port)
;;
;; Establishes a socket connection to PIDA.
(defun pida-connect (port)
  (setq pida-connection
	(open-network-stream "pida-connection" nil "localhost" port))
  (process-kill-without-query pida-connection nil)
  (pida-register-hooks)
  (pida-send-message "pida-ping ready"))

;; pida-disconnect
;;
;; Closes socket connection to PIDA.
(defun pida-disconnect ()
  (pida-send-message "kill-emacs-hook")
  (if (pida-check-connection)
      (delete-process pida-connection))
  ;; Delete all clients first.
  (while server-clients
    (server-delete-client (car server-clients)))
  (server-start 1)
  (pida-unregister-hooks))

;; pida-ping
;;
;; Used to check status of Emacs.
(defun pida-ping ()
  (pida-send-message "pida-pong ready"))


;; pida-frame-setup
;;
;; Removes menu bar and tool bar from given frame.
(defun pida-frame-setup (frame)
  (modify-frame-parameters frame
			   '((menu-bar-lines . nil)))
  (modify-frame-parameters frame
			   '((tool-bar-lines . nil))))

;; pida-find-file
;; 
;; Callback function of find-file-hooks.
(defun pida-find-file ()
  (pida-send-message (concat "find-file-hooks " buffer-file-name)))

;; pida-kill-buffer
;;
;; Callback function of kill-buffer-hook.
(defun pida-kill-buffer ()
  (pida-send-message (concat "kill-buffer-hook " buffer-file-name)))

;; pida-after-save
;;
;; Callback function of after-save-hook.
(defun pida-after-save ()
  (pida-send-message (concat "after-save-hook " buffer-file-name)))


;; pida-window-configuration-change
;;
;; Callback function of window-configuration-change-hook.
(defun pida-window-configuration-change ()
  (setq completion-function 'mycomplete-wrapper)
  (pida-send-message (concat "window-configuration-change-hook "
			     buffer-file-name)))

;; pida-kill-emacs
;;
;; Callback function of kill-emacs-hook.
(defun pida-kill-emacs ()
  (pida-disconnect))

;; pida-goto-line
;;
;; called by pida:  goto-line 
(defun pida-goto-line (bufn line)
  (set-buffer (get-file-buffer bufn))
  (goto-line line))


;; pida-save-buffer
;; 
;; called by pida to save buffer
(defun pida-save-buffer (buffn)
  (set-buffer (get-file-buffer buffn))
  (save-buffer))

;; pida-save-buffer-as
;; 
;; called by pida to save buffer as new file
(defun pida-save-buffer (buffn filen)
  (set-buffer (get-file-buffer buffn))
  (write-file filen))

;; pida-cut
;; 
;; called by pida to cut region
(defun pida-cut (buffn)
  (set-buffer (get-file-buffer buffn))
  (kill-region (region-beginning) (region-end)))

;; pida-copy
;; 
;; called by pida to copy region 
(defun pida-copy (buffn)
  (set-buffer (get-file-buffer buffn))
  (kill-ring-save (region-beginning) (region-end)))

;; pida-save-buffer-as
;; 
;; called by pida to paste 
(defun pida-paste (buffn)
  (set-buffer (get-file-buffer buffn))
  (yank))


(setq inhibit-splash-screen 1)

(require 'dbus)

(defun collabora-browser-introspect ()
  "The collaborative editing browser interface"
  "<node name='/Test'>
  <interface name='org.freedesktop.DBus.Introspectable'>
    <method name='Introspect'>
      <arg name='xml_data' type='s' direction='out'/>
    </method>
  </interface>
  <interface name='uk.co.pida.emacs.Test'>
    <method name='Open'>
      <arg direction='in' type='s' name='file-name'/>
    </method>
  </interface>
</node>")



(dbus-register-method
 :session dbus-service-emacs "/Test"
 dbus-interface-introspectable "Introspect" 'collabora-browser-introspect)
