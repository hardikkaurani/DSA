import java.util.*;

class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in); 

        int n = sc.nextInt(); 
        int[] a = new int[n];

        for(int i=0;i<n;i++) a[i]=sc.nextInt(); 

        int t = sc.nextInt(); 

        HashMap<Integer,Integer> m = new HashMap<>();

        for(int i=0;i<n;i++){
            int x = t - a[i]; 

            if(m.containsKey(x)){
                System.out.println(m.get(x) + " " + i); 
                return;
            }

            m.put(a[i], i); 
        }
    }
}